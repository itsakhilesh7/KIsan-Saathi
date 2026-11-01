import json
import logging
from collections import OrderedDict

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from . import config, pipeline, whatsapp

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("main")

app = FastAPI(title="Kisan Saathi")

# Meta retries webhooks that are slow to answer, so de-duplicate by message id.
_SEEN: "OrderedDict[str, None]" = OrderedDict()
_SEEN_MAX = 2000


def _is_duplicate(msg_id: str | None) -> bool:
    if not msg_id:
        return False
    if msg_id in _SEEN:
        return True
    _SEEN[msg_id] = None
    if len(_SEEN) > _SEEN_MAX:
        _SEEN.popitem(last=False)
    return False


@app.get("/health")
async def health():
    return {"ok": True, "llm_mode": "evon" if config.LLM_BASE_URL else "echo"}


@app.get("/webhook")
async def verify(
    mode: str = Query(None, alias="hub.mode"),
    token: str = Query(None, alias="hub.verify_token"),
    challenge: str = Query(None, alias="hub.challenge"),
):
    if mode == "subscribe" and token and token == config.WA_VERIFY_TOKEN:
        return PlainTextResponse(challenge or "")
    raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook")
async def receive(request: Request, background: BackgroundTasks):
    raw = await request.body()
    if not whatsapp.verify_signature(raw, request.headers.get("X-Hub-Signature-256")):
        raise HTTPException(status_code=403, detail="Bad signature")
    try:
        payload = json.loads(raw)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    for msg in whatsapp.extract_messages(payload):
        if _is_duplicate(msg["id"]):
            continue
        background.add_task(pipeline.handle_message, msg)
    return {"status": "ok"}  # answer fast; work happens in the background
