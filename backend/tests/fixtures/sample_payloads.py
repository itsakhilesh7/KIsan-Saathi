"""Test fixtures and mock payloads for unit tests."""

def make_whatsapp_payload(msg_id: str = "wamid.test_1", mtype: str = "audio", from_num: str = "919999999999") -> dict:
    """Creates a mock WhatsApp webhook inbound payload."""
    msg: dict = {"id": msg_id, "from": from_num, "type": mtype, "timestamp": "1730467200"}
    if mtype == "audio":
        msg["audio"] = {"id": "MEDIA_ID_123", "mime_type": "audio/ogg; codecs=opus"}
    elif mtype == "text":
        msg["text"] = {"body": "వారంగల్ మార్కెట్‌లో పత్తి ధర ఎంత?"}

    return {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [msg],
                            "messaging_product": "whatsapp",
                        }
                    }
                ]
            }
        ]
    }
