# Phase 2 WhatsApp Live Loop Checklist

This document details the exact manual steps for testing the Kisan Saathi live WhatsApp loop on Windows.

---

## 1. Prerequisites on Windows

1. **Python Virtual Environment** activated:
   ```powershell
   .\existing-code\.venv\Scripts\Activate.ps1
   ```
2. **Tunneling Tool** installed (`ngrok` or `cloudflared`):
   ```powershell
   # If not installed, install via winget:
   winget install ngrok.ngrok
   # or
   winget install Cloudflare.cloudflared
   ```
3. **FFmpeg installed on Windows**:
   ```powershell
   winget install Gyan.FFmpeg
   # Verify in a new terminal:
   ffmpeg -version
   ```
4. **Meta Developer Account**:
   - Access: https://developers.facebook.com/apps/
   - WhatsApp App created (type: Business).

---

## 2. Step-by-Step Execution

### Step 1: Start the Local Backend Server
In PowerShell:
```powershell
.\existing-code\.venv\Scripts\python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
Verify health locally:
```powershell
curl http://localhost:8000/api/health
```

---

### Step 2: Open a Public Tunnel
In a second PowerShell window:

**Option A: Using ngrok**
```powershell
ngrok http 8000
```
*Note the public HTTPS forwarding URL (e.g., `https://1a2b-3c4d.ngrok-free.app`).*

**Option B: Using Cloudflare Tunnel**
```powershell
cloudflared tunnel --url http://localhost:8000
```
*Note the public HTTPS URL (e.g., `https://random-name.trycloudflare.com`).*

---

### Step 3: Configure Meta Webhook URL & Verify Token
1. Go to **Meta Developer Portal > Your App > WhatsApp > Configuration**.
2. Click **Edit** under **Webhook**:
   - **Callback URL**: `https://<your-tunnel-subdomain>/webhook`
   - **Verify Token**: Must match `WHATSAPP_VERIFY_TOKEN` in `backend/.env`.
3. Click **Verify and Save**.
4. **Expected Server Log:**
   ```text
   INFO:     127.0.0.1:xxxxx - "GET /webhook?hub.mode=subscribe&hub.challenge=11223344&hub.verify_token=... HTTP/1.1" 200 OK
   ```

---

### Step 4: Subscribe to the `messages` Webhook Field
1. In the same **Webhook** section on Meta Developer Portal, click **Manage Webhook Fields**.
2. Locate the row **messages**.
3. Click **Subscribe** (toggle should show Subscribed / Active).

---

### Step 5: Update `backend/.env` with Live Meta & Gnani Credentials
Fill in `backend/.env` with your real secrets:
```bash
# App security
APP_ENV=development
PHONE_HASH_SALT=your_custom_salt_here

# Meta Cloud API
META_APP_SECRET=your_app_secret_from_app_settings_basic
WHATSAPP_VERIFY_TOKEN=your_chosen_verify_token
WHATSAPP_ACCESS_TOKEN=your_temporary_or_system_user_token
WHATSAPP_PHONE_NUMBER_ID=your_test_phone_number_id
WHATSAPP_BUSINESS_ACCOUNT_ID=your_waba_id

# Gnani Voice Services
GNANI_API_KEY=your_gnani_api_key_from_app_gnani_ai
```

> **Note on Tokens:** Temporary tokens expire in 24 hours. When testing resumes on a new day, go to **WhatsApp > API Setup**, click **Generate Token**, and update `WHATSAPP_ACCESS_TOKEN` in `backend/.env`.

---

### Step 6: Verify Recipient Phone Number
Meta test numbers can only send to verified phone numbers:
1. In **WhatsApp > API Setup**, scroll to **To** dropdown.
2. Click **Manage phone number list** -> Add your personal phone number.
3. Enter the 6-digit OTP code sent via WhatsApp to verify your number.

---

### Step 7: Test 1 — Inbound Text Message
1. Send a text message (e.g., `"Namaskaram"`) from your phone to the Meta test WhatsApp number.
2. Check terminal logs:
   ```text
   INFO:     Received webhook entry with 1 changes
   INFO:     Dispatched background task for sender=...
   INFO:     Text message received: 'Namaskaram'
   ```
3. Your phone receives a reply text.

---

### Step 8: Test 2 — Inbound Voice Note (Audio Loop)
1. Record a short 5–10 second voice note on WhatsApp (e.g., *"వరంగల్ లో పత్తి ధర ఎంత?"* or *"Namaskaram"*).
2. Send it to the Meta test number.

---

## 3. What a Success Log Line Looks Like

During an end-to-end voice note execution, the backend logs each stage timing and event:

```text
INFO:     [orchestrator] Processing voice message media_id='1029384756' mime='audio/ogg; codecs=opus' from_hash='a1b2c3d4...'
INFO:     [whatsapp] Downloaded media 28410 bytes in 0.42s
INFO:     [audio] Converted in.ogg -> 16kHz in.wav (duration: 6.4s)
INFO:     [gnani.stt] STT completed in 1.15s: transcript='వరంగల్ లో పత్తి ధర ఎంత' detected_lang='te-IN'
INFO:     [llm] LLM mode='echo' (or 'gnani-evon') response generated in 0.25s
INFO:     [gnani.tts] Synthesized 96000 bytes audio using voice='Lavanya' lang='te-IN' in 1.82s
INFO:     [audio] Converted out.wav -> out.ogg (Opus 24kbps) in 0.18s
INFO:     [whatsapp] Uploaded reply media_id='9988776655' in 0.35s
INFO:     [whatsapp] Sent voice note audio reply to user
INFO:     [events] Logged request_id='req_xyz789' status='ok' total_time=4.17s
```

On your phone, you should see:
1. An audio voice note message playable with inline waveform.
2. A text copy of the transcript/answer (if `SEND_TEXT_COPY=True`).
