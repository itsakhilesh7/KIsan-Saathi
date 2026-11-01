# WhatsApp Cloud API Integration Notes

Based on Meta's "WhatsApp Cloud API Get Started" and audio-message docs (checked 1 Nov 2026). The dashboard UI changes often; if a step differs, describe it and adapt.

## Setup (done by the developer, not the agent)
1. Meta developer account -> create app -> add WhatsApp product -> API Setup page.
2. A **free test business number** is provided. Add recipients under "Manage phone number list" (**up to 5**); each receives a code in WhatsApp to verify.
3. Send the `hello_world` template; **reply to it** to open the customer-service window.
4. Note: `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_BUSINESS_ACCOUNT_ID`, app secret (App settings -> Basic).
5. The temporary token on the API Setup page expires within hours to a day. For the demo create a **System User** token in Business Settings with permissions `whatsapp_business_messaging` and `business_management`.
6. Do **not** register a personal number as the sender; a number on the API generally cannot also be used in the normal WhatsApp app.

## Webhook
- `GET /webhook` verification: params `hub.mode=subscribe`, `hub.verify_token`, `hub.challenge`; return the challenge as plain text if the token matches, else 403.
- `POST /webhook`: JSON `entry[].changes[].value.messages[]` with `type` in {text, audio, ...}; audio has `audio.id`. `value.statuses` are delivery receipts: ignore.
- Verify `X-Hub-Signature-256` = `sha256=` + HMAC-SHA256(app secret, raw body). Compare in constant time.
- Subscribe to the **messages** field in the dashboard.
- Meta retries slow webhooks: acknowledge within seconds, process in the background, **dedupe by message id**.
- Local development needs a public HTTPS URL (Cloudflare Tunnel or ngrok). Replace with the deployed URL in Phase 6.

## Media
- Incoming voice note: `GET {graph}/{media_id}` with `Authorization: Bearer <token>` returns `{url, mime_type, ...}`; then `GET url` with the same bearer header returns bytes (OGG/Opus).
- Outgoing voice note: upload `POST {graph}/{phone_number_id}/media` multipart (`file`, `type=audio/ogg`, `messaging_product=whatsapp`) -> media id; then send `{"type":"audio","audio":{"id":...}}`.
- **Voice messages must be OGG encoded with the OPUS codec, mono, up to 16 MB. The inline play icon appears only if the file is <= 512 KB**, so keep replies short. ffmpeg: `-ac 1 -ar 24000 -c:a libopus -b:a 24k -application voip`.
- Graph version is configurable (`WA_API_VERSION`, docs showed v23.0).

## Rules of the platform that shape the product
- Free-form replies (including audio) are allowed only within **24 hours of the user's last message**. Our flows are user-initiated, so this is fine; never message first without a template.
- Only verified recipients can message the **test** number. **Judges cannot use it**, which is why the web demo is mandatory.
- WhatsApp Business **Calling API** exists (Meta docs link from the Get Started page). Not used in the MVP; needs extra setup and a verified business.
- Telegram fallback: if Meta onboarding stalls past Phase 2, implement `channels/telegram/` (bot token via BotFather) against the same orchestrator.
- SMS: skipped (India DLT registration overhead).

## Test checklist (live; record evidence)
Text echo; voice echo; voice note longer than 30 s; Telugu/Hindi/English notes; duplicate webhook delivery; bad signature rejected; failure path sends a fallback message; token-expiry error is logged clearly.
