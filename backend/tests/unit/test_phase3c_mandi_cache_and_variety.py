"""Unit tests for Phase 3C Mandi Cache, State-Level Fallback, and Variety/Grade Handling."""

from backend.app.integrations.data_gov.mandi_cache import MandiCache
from backend.app.schemas.evidence import Evidence, SourceType
from backend.app.services.answer_composer import compose_mandi_answer


def test_mandi_cache_lifecycle(tmp_path):
    """Test saving to and querying from SQLite MandiCache."""
    db_file = tmp_path / "test_mandi_cache.sqlite3"
    cache = MandiCache(db_path=str(db_file))

    ev1 = Evidence(
        evidence_id="mandi_warangal_cotton_1",
        source_type=SourceType.MANDI_RECORD,
        source_name="Agmarknet",
        source_url="https://api.data.gov.in/test",
        publisher="DMI",
        observation_or_publication_date="2026-11-04",
        location="Warangal, Warangal, Telangana",
        data={
            "state": "Telangana",
            "district": "Warangal",
            "market": "Warangal",
            "commodity": "Cotton",
            "variety": "Other",
            "grade": "FAQ",
            "arrival_date": "2026-11-04",
            "modal_price": 7200.0,
            "min_price": 7000.0,
            "max_price": 7400.0,
        },
    )

    cache.save_evidence([ev1])

    # Query matching exact district and commodity
    results = cache.query_cached(state="Telangana", district="Warangal", commodity="Cotton")
    assert len(results) == 1
    assert results[0].data["modal_price"] == 7200.0
    assert results[0].data["cached"] is True
    assert "cached_retrieved_at" in results[0].data

    # Query non-matching district returns empty
    results_empty = cache.query_cached(state="Telangana", district="Karimnagar", commodity="Cotton")
    assert len(results_empty) == 0

    # Query state level (district=None) returns cached record
    results_state = cache.query_cached(state="Telangana", district=None, commodity="Cotton")
    assert len(results_state) == 1


def test_variety_and_grade_distinction_never_mixed():
    """Verify that when a market has distinct varieties, the composer names them explicitly."""
    ev_common = Evidence(
        evidence_id="paddy_common",
        source_type=SourceType.MANDI_RECORD,
        source_name="Agmarknet",
        source_url="https://api.data.gov.in/test",
        publisher="DMI",
        observation_or_publication_date="2026-11-05",
        location="Cherial, Warangal, Telangana",
        data={
            "state": "Telangana",
            "district": "Warangal",
            "market": "Cherial",
            "commodity": "Paddy",
            "variety": "Common",
            "arrival_date": "2026-11-05",
            "modal_price": 2369.0,
        },
    )

    ev_fine = Evidence(
        evidence_id="paddy_fine",
        source_type=SourceType.MANDI_RECORD,
        source_name="Agmarknet",
        source_url="https://api.data.gov.in/test",
        publisher="DMI",
        observation_or_publication_date="2026-11-05",
        location="Cherial, Warangal, Telangana",
        data={
            "state": "Telangana",
            "district": "Warangal",
            "market": "Cherial",
            "commodity": "Paddy",
            "variety": "Fine/Superfine/Grade A",
            "arrival_date": "2026-11-05",
            "modal_price": 2700.0,
        },
    )

    # In Telugu
    ans_te = compose_mandi_answer(
        evidence_list=[ev_common, ev_fine],
        language="te-IN",
        requested_district="Warangal",
        requested_commodity="Paddy",
        unit="Rs per quintal",
    )
    # Both numbers must appear and be verified
    assert "2369" in ans_te
    assert "2700" in ans_te
    assert "Cherial" in ans_te
    assert "క్వింటాలుకు" in ans_te

    # In English
    ans_en = compose_mandi_answer(
        evidence_list=[ev_common, ev_fine],
        language="en-IN",
        requested_district="Warangal",
        requested_commodity="Paddy",
        unit="Rs per quintal",
    )
    assert "2369" in ans_en
    assert "2700" in ans_en
    assert "Cherial" in ans_en
    assert "per quintal" in ans_en


def test_mandi_cached_and_state_fallback_notes():
    """Verify that cached data notes and state fallback prefixes are added naturally."""
    ev_state_cached = Evidence(
        evidence_id="cotton_state",
        source_type=SourceType.MANDI_RECORD,
        source_name="Agmarknet",
        source_url="https://api.data.gov.in/test",
        publisher="DMI",
        observation_or_publication_date="2026-11-04",
        location="Adilabad, Adilabad, Telangana",
        data={
            "state": "Telangana",
            "district": "Adilabad",
            "market": "Adilabad",
            "commodity": "Cotton",
            "arrival_date": "2026-11-04",
            "modal_price": 7400.0,
            "cached": True,
            "is_state_fallback": True,
        },
    )

    ans = compose_mandi_answer(
        evidence_list=[ev_state_cached],
        language="te-IN",
        requested_district="Warangal",
        requested_commodity="Cotton",
        unit="Rs per quintal",
    )
    # Must mention state level fallback and cached note
    assert "తెలంగాణ రాష్ట్ర స్థాయి" in ans
    assert "గమనిక" in ans
    assert "7400" in ans
    assert "క్వింటాలుకు" in ans
