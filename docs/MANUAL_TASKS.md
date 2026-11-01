# Manual Tasks Checklist for Developer

This checklist tracks all tasks that require human action, developer credentials, physical hardware, or portal access. The AI agent cannot perform these tasks.

---

### Priority 1: Day 1 Blockers (Required for Phase 0 & Phase 1 Live Verification)

- [ ] **Task 1: Obtain Gnani API Key & Add to `.env`**
  - **Why:** Required to verify Prisma STT and Timbre TTS live against real endpoints.
  - **Where:** Log in to https://app.gnani.ai/voice/ and generate an API key with voice services enabled.
  - **Action:** Copy key into `backend/.env`:
    ```bash
    GNANI_API_KEY=your_gnani_api_key_here
    ```
  - **Verification:** Run `python -m backend.scripts.test_gnani --tts "నమస్కారం" --lang te-IN` in Windows terminal.

- [ ] **Task 2: Install FFmpeg & FFprobe on Windows**
  - **Why:** Required for audio transcoding (OGG/Opus <-> WAV 16kHz) and clip chunking.
  - **Action (PowerShell / Windows Package Manager):**
    ```powershell
    winget install Gyan.FFmpeg
    ```
  - **Verification:** Restart terminal and run:
    ```powershell
    ffmpeg -version
    ffprobe -version
    ```

- [ ] **Task 3: Meta Developer Account & WhatsApp Test Recipient Setup**
  - **Why:** Required for Phase 2 (WhatsApp live loop).
  - **Where:** https://developers.facebook.com/
  - **Steps:**
    1. Create an app (type: Business) and add WhatsApp product.
    2. Go to **WhatsApp > API Setup** to get:
       - Temporary Access Token (or generate a permanent System User Token)
       - Phone Number ID
       - WhatsApp Business Account ID
    3. Under "To" phone numbers, add your personal phone number as a **Verified Recipient** (Meta sends an OTP).
    4. Note the **App Secret** from App Settings > Basic.
    5. Copy into `backend/.env`:
       ```bash
       WHATSAPP_PHONE_NUMBER_ID=...
       WHATSAPP_BUSINESS_ACCOUNT_ID=...
       WHATSAPP_ACCESS_TOKEN=...
       WHATSAPP_VERIFY_TOKEN=choose_a_random_string
       META_APP_SECRET=...
       ```

- [ ] **Task 4: Clarify Evon Access on Gnani Discord / Support**
  - **Why:** Decision D-009 depends on whether Gnani hosts `gnani-evon-v3.3-30B-A3B` via REST API or if self-hosting is required.
  - **Action:** Post in the Gnani internship challenge Discord:
    *"Does Gnani provide an OpenAI-compatible REST endpoint for Evon v3.3-30B for challenge participants, or should we run it via vLLM on a rented GPU?"*

---

### Priority 2: Agricultural & Grounding Data (Required for Phase 3 & 4)

- [ ] **Task 5: Obtain data.gov.in API Key & Verify Live Mandi Resource**
  - **Why:** Live mandi price queries depend on Agmarknet data.
  - **Where:** Register at https://data.gov.in/ to get a free API key.
  - **Action:** Add `DATA_GOV_API_KEY=...` to `backend/.env`.
  - **Verification Command (PowerShell):**
    ```powershell
    curl.exe "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070?api-key=YOUR_KEY&format=json&limit=5"
    ```
    Confirm response JSON format, field names (e.g. `state`, `district`, `market`, `commodity`, `modal_price`).

- [ ] **Task 6: Locate Kisan Call Centre (KCC) Resource IDs on data.gov.in**
  - **Why:** Corpus retrieval for grounded crop Q&A (Phase 4).
  - **Action:** Search data.gov.in for "Kisan Call Centre" datasets for the pilot state (Telangana / Andhra Pradesh). Add comma-separated resource IDs to `KCC_RESOURCE_IDS` in `backend/.env`.

- [ ] **Task 7: Confirm Pilot Region & Commodities in `config/pilot.yaml`**
  - **Why:** Default proposed is Telangana/Warangal with cotton, chilli, paddy.
  - **Action:** Inspect the live data.gov.in output for Warangal markets. Update `markets:` list in `config/pilot.yaml` with exact matching strings, then set `confirmed: true`.

---

### Priority 3: Evaluation Dataset (Required for Phase 1 & 6)

- [ ] **Task 8: Record 10 Reference Telugu / Hindi Audio Clips with Transcripts**
  - **Why:** Baseline WER/CER measurement requires local audio with known ground truth.
  - **Action:**
    1. Record 10 voice notes (5 Telugu, 5 Hindi/Hinglish) using a phone voice recorder.
    2. Save files into `backend/data/clips/` (or `evaluation/audio_samples/`).
    3. Update `backend/data/transcripts.csv` with filename, language, and exact text reference.
  - **Verification:** Run `python -m backend.scripts.eval_wer`.

---

### Priority 4: Late-Stage Infrastructure (Phase 5 & 6)

- [ ] **Task 9: GPU Rental for Evon (if self-hosted)**
  - **Why:** If Gnani does not provide hosted Evon, rent an A10G/A100 or RunPod/Vast.ai instance (~24 GB VRAM) running vLLM.
- [ ] **Task 10: Cloud Deployment Setup (Render / Railway & Vercel)**
  - **Why:** Public web demo and public WhatsApp webhook URL require external hosting.
