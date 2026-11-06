"""Unit tests reproducing and verifying the Mandi cache lifecycle bug and graceful API failure.

Requirements:
- fetch_mandi_prices called with NO explicit cache (cache=None) must populate the cache on success.
- Subsequent 502 / timeout must be answered from the cache with the date caveat.
- If API fails and cache is empty, reply with specific message ('the price service is not responding right now...'),
  not the generic fallback.
"""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from backend.app.core.config import Settings
from backend.app.core.messages import get_message
from backend.app.integrations.data_gov.mandi import (
    MandiServiceUnavailableError,
    fetch_mandi_prices,
)
from backend.app.integrations.data_gov.mandi_cache import MandiCache
from backend.app.services.answer_composer import compose_mandi_answer
from backend.app.services.orchestrator import handle_text_message


@pytest.mark.asyncio
async def test_mandi_cache_populated_with_no_explicit_cache_argument(tmp_path):
    """Calling fetch_mandi_prices with cache=None must save to active_cache and serve 502 from cache."""
    test_db = str(tmp_path / "test_mandi_cache.sqlite3")
    local_cache = MandiCache(db_path=test_db)

    # Patch get_mandi_cache so fetch_mandi_prices uses our test DB
    with patch("backend.app.integrations.data_gov.mandi.get_mandi_cache", return_value=local_cache), \
         patch("asyncio.sleep", new_callable=AsyncMock):
        settings = Settings(

            DATA_GOV_API_KEY="test_key",
            DATA_GOV_BASE_URL="https://api.data.gov.in/resource",
            MANDI_RESOURCE_ID="test_res",
            MANDI_PRICE_UNIT="per quintal",
        )

        mock_200 = AsyncMock(spec=httpx.AsyncClient)
        mock_response = httpx.Response(
            200,
            json={
                "status": "ok",
                "total": "1",
                "count": "1",
                "limit": "20",
                "offset": "0",
                "records": [
                    {
                        "state": "Telangana",
                        "district": "Warangal",
                        "market": "Warangal",
                        "commodity": "Cotton",
                        "variety": "Other",
                        "grade": "FAQ",
                        "arrival_date": "04/11/2026",
                        "min_price": "7000",
                        "max_price": "7400",
                        "modal_price": "7200",
                    }
                ],
            },
            request=httpx.Request("GET", "https://api.data.gov.in/test"),
        )
        mock_200.get = AsyncMock(return_value=mock_response)

        # Call 1: Live call succeeds with cache=None (standard usage)
        evidence = await fetch_mandi_prices(
            commodity="Cotton",
            district="Warangal",
            state="Telangana",
            settings=settings,
            client=mock_200,
            cache=None,
            use_cache=True,
        )

        assert len(evidence) == 1
        assert evidence[0].data["modal_price"] == 7200.0

        # Verify that active_cache was indeed populated!
        cached_items = local_cache.query_cached(state="Telangana", district="Warangal", commodity="Cotton")
        assert len(cached_items) == 1, "Cache was not populated when cache=None was passed!"
        assert cached_items[0].data["modal_price"] == 7200.0

        # Call 2: Simulated 502 Bad Gateway with cache=None
        mock_502 = AsyncMock(spec=httpx.AsyncClient)
        mock_502_resp = httpx.Response(
            502,
            request=httpx.Request("GET", "https://api.data.gov.in/test"),
        )
        mock_502.get = AsyncMock(return_value=mock_502_resp)

        evidence_from_cache = await fetch_mandi_prices(
            commodity="Cotton",
            district="Warangal",
            state="Telangana",
            settings=settings,
            client=mock_502,
            cache=None,
            use_cache=True,
        )

        assert len(evidence_from_cache) == 1
        assert evidence_from_cache[0].data["cached"] is True
        assert evidence_from_cache[0].data["modal_price"] == 7200.0

        # Verify composed answer contains date caveat for cached record
        ans_te = compose_mandi_answer(
            evidence_from_cache,
            language="te-IN",
            requested_district="Warangal",
            requested_commodity="Cotton",
        )
        assert "మునుపటి రికార్డు" in ans_te or "గమనిక" in ans_te
        assert "7200" in ans_te

        ans_en = compose_mandi_answer(
            evidence_from_cache,
            language="en-IN",
            requested_district="Warangal",
            requested_commodity="Cotton",
        )
        assert "showing record from" in ans_en.lower() or "note" in ans_en.lower()
        assert "7200" in ans_en


@pytest.mark.asyncio
async def test_mandi_empty_cache_and_api_failure_replies_specific_message(tmp_path):
    """If API fails and cache is empty, must raise MandiServiceUnavailableError and reply with specific message."""
    test_db = str(tmp_path / "empty_cache.sqlite3")
    empty_cache = MandiCache(db_path=test_db)

    with patch("backend.app.integrations.data_gov.mandi.get_mandi_cache", return_value=empty_cache), \
         patch("asyncio.sleep", new_callable=AsyncMock):
        settings = Settings(

            DATA_GOV_API_KEY="test_key",
            DATA_GOV_BASE_URL="https://api.data.gov.in/resource",
            MANDI_RESOURCE_ID="test_res",
        )

        mock_502 = AsyncMock(spec=httpx.AsyncClient)
        mock_502_resp = httpx.Response(502, request=httpx.Request("GET", "https://api.data.gov.in/test"))
        mock_502.get = AsyncMock(return_value=mock_502_resp)

        # 1. Direct call raises MandiServiceUnavailableError
        with pytest.raises(MandiServiceUnavailableError):
            await fetch_mandi_prices(
                commodity="Cotton",
                district="Warangal",
                state="Telangana",
                settings=settings,
                client=mock_502,
                cache=None,
                use_cache=True,
            )

        # 2. End-to-end via handle_text_message produces specific service unavailable message in user's language
        mock_channel = AsyncMock()
        mock_channel.channel_name = "test_channel"
        mock_channel.send_text = AsyncMock()

        msg = {
            "from": "919876543210",
            "text": "What is the price of cotton in Warangal?",
        }

        # Patch fetch_mandi_prices to raise MandiServiceUnavailableError
        with patch("backend.app.services.orchestrator.fetch_mandi_prices", side_effect=MandiServiceUnavailableError("Service down")):
            await handle_text_message(msg, settings=settings, client=mock_channel)

            assert mock_channel.send_text.called
            sent_phone, sent_text = mock_channel.send_text.call_args[0][:2]
            expected_en = get_message("mandi_service_unavailable", "en-IN")
            assert sent_text == expected_en
            assert "1551" not in sent_text, "Should not return generic 1551 fallback when mandi service is specifically down"
