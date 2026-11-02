"""Shared outbound HTTP client management for connection pooling and reuse."""

import httpx

_SHARED_CLIENT: httpx.AsyncClient | None = None


def get_http_client() -> httpx.AsyncClient:
    """Returns the shared httpx.AsyncClient instance, creating one if needed."""
    global _SHARED_CLIENT
    if _SHARED_CLIENT is None or _SHARED_CLIENT.is_closed:
        _SHARED_CLIENT = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0, connect=10.0, read=60.0, write=30.0),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=50),
        )
    return _SHARED_CLIENT


async def close_http_client() -> None:
    """Closes the shared httpx.AsyncClient connection pool."""
    global _SHARED_CLIENT
    if _SHARED_CLIENT is not None and not _SHARED_CLIENT.is_closed:
        await _SHARED_CLIENT.aclose()
        _SHARED_CLIENT = None
