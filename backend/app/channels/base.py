"""ChannelClient protocol and default WhatsApp channel adapter."""

from typing import Any, Protocol, runtime_checkable

from ..core.config import Settings
from .whatsapp import client as wa_client


@runtime_checkable
class ChannelClient(Protocol):
    """Abstract interface for messaging channel clients (WhatsApp, Telegram, etc.)."""

    channel_name: str

    async def download_media(self, media_id: str) -> bytes:
        """Downloads audio media bytes for the given media_id / file_id."""
        ...

    async def send_text(self, to: str, text: str) -> Any:
        """Sends a text message to the given user / chat ID."""
        ...

    async def send_audio_bytes(self, to: str, audio_bytes: bytes) -> Any:
        """Sends a voice note (OGG/Opus mono) to the given user / chat ID."""
        ...


class WhatsAppChannelClient:
    """ChannelClient implementation for Meta WhatsApp Cloud API."""

    channel_name: str = "whatsapp"

    def __init__(self, settings: Settings | None = None):
        self.settings = settings

    async def download_media(self, media_id: str) -> bytes:
        return await wa_client.download_media(media_id, settings=self.settings)

    async def send_text(self, to: str, text: str) -> Any:
        return await wa_client.send_text(to, text, settings=self.settings)

    async def send_audio_bytes(self, to: str, audio_bytes: bytes) -> Any:
        reply_media_id = await wa_client.upload_audio(audio_bytes, settings=self.settings)
        return await wa_client.send_audio(to, reply_media_id, settings=self.settings)
