"""Voice API endpoints (architecture.md §6.3)."""

from fastapi import APIRouter

from ...schemas.conversation import VoiceRequest, VoiceResponse

router = APIRouter(prefix="/api/voice", tags=["voice"])


@router.post("/query", response_model=VoiceResponse)
async def query_voice(request: VoiceRequest) -> VoiceResponse:
    """Processes voice or text query for the web demo channel.

    Full implementation wired in Phase 5 (Web Demo).
    """
    return VoiceResponse(
        request_id=request.request_id,
        transcript=request.text,
        language=request.language or "te-IN",
        needs_clarification=False,
    )
