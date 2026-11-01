# Kisan Saathi (కిసాన్ సాథీ / किसान साथी)

> **Voice-first agricultural advisory assistant for Indian farmers on WhatsApp and Web**  
> Built for the Gnani "Great Indian AI Internship" challenge (November 2026).

---

## 1. What is Kisan Saathi?

Kisan Saathi is a source-grounded voice assistant designed specifically for Indian smallholder farmers. Farmers interact naturally by sending voice notes on WhatsApp in **Telugu**, **Hindi**, or **English** (with Hinglish support). The system listens, retrieves grounded facts from official data sources, reasons with an LLM, and speaks back a concise, actionable answer as an audio voice note.

### Core Pipeline
```
[ WhatsApp Voice Note (OGG/Opus) ]
                │
                ▼
      [ FFmpeg Transcoding ]  ──> 16 kHz Mono WAV
                │
                ▼
   [ Gnani Prisma STT v3.0 ]  ──> Auto Language Detect + Transcript
                │
                ▼
       [ Orchestrator ]       ──> Intent & Entity Extraction
                │
                ├──> Mandi Saathi   (data.gov.in Agmarknet daily wholesale prices)
                ├──> Weather Saathi (Open-Meteo local forecasts)
                └──> Crop Saathi    (Kisan Call Centre historical Q&A retrieval)
                │
                ▼
      [ Gnani Evon LLM ]      ──> Grounded Reasoning (Strict refusal of synthetic doses)
                │
                ▼
   [ Gnani Timbre TTS v2.5 ]  ──> Native Spoken Audio (WAV 48 kHz)
                │
                ▼
      [ FFmpeg Transcoding ]  ──> OGG/Opus Mono (voip mode, <= 512 KB)
                │
                ▼
[ Spoken Voice Note + Text Reply to Farmer ]
```

### Safety and Grounding Invariants (rules.md)
- **Zero Hallucinated Facts:** Every price, weather forecast, or crop advisory claim is strictly bound to retrieved evidence records.
- **Strict Chemical Dose Refusal:** Chemical doses, mixtures, or spray schedules are **never** generated from model weights. Farmers requesting doses are politely referred to the national **1551 Kisan Call Centre helpline** and local Krishi Vigyan Kendras (KVK).
- **Privacy by Design:** Farmer mobile numbers are hashed with a secret salt (`PHONE_HASH_SALT`). Raw phone numbers and private voice audio are never committed or logged in plaintext.

---

## 2. Architecture & Directory Layout

```mermaid
flowchart TD
    User([Farmer on WhatsApp]) <-->|Voice Note OGG| WA[WhatsApp Cloud API Webhook]
    Judge([Evaluator / Web Demo]) <-->|Audio / Text| WebAPI[FastAPI /api/voice/query]
    
    subgraph Backend [FastAPI Application]
        WA --> Sec[Signature & Dedup]
        Sec --> Orch[Orchestrator Service]
        WebAPI --> Orch
        
        Orch --> AudioServ[Audio Service / FFmpeg]
        AudioServ --> STT[Gnani Prisma STT v3.0]
        STT --> Intent[Intent & Slot Extraction]
        
        Intent --> ToolMandi[Mandi Tool / data.gov.in]
        Intent --> ToolWeather[Weather Tool / Open-Meteo]
        Intent --> ToolKCC[Crop Tool / KCC Retrieval]
        
        ToolMandi --> LLM[Evon LLM Adapter]
        ToolWeather --> LLM
        ToolKCC --> LLM
        
        LLM --> TTS[Gnani Timbre TTS v2.5/v3.0]
        TTS --> AudioServ
    end
```

### Directory Structure
```text
├── config/
│   ├── pilot.example.yaml     # Reference pilot configuration
│   └── pilot.yaml             # Local active pilot config (confirmed: false)
├── docs/
│   ├── code-audit.md          # Comprehensive audit of starter code
│   ├── decisions.md           # Architecture Decision Records (ADRs)
│   ├── gnani-api-notes.md     # Verified Gnani API endpoints & models
│   ├── MANUAL_TASKS.md        # Action checklist for developer credentials
│   ├── PACK_README.md         # Original planning pack documentation
│   ├── PROGRESS.md            # Living project log for human & AI reviewers
│   └── whatsapp-integration.md# Meta Cloud API integration guide
├── existing-code/             # Immutable reference snapshot of starter code
├── backend/
│   ├── app/
│   │   ├── api/routes/        # REST routes (health, voice, mandi, weather)
│   │   ├── channels/whatsapp/ # Webhook, signature check, deduplication, client
│   │   ├── core/              # Typed Settings, structured logging, security
│   │   ├── integrations/
│   │   │   ├── gnani/         # Prisma STT & Timbre TTS adapters
│   │   │   └── llm/           # OpenAI-compatible LLM adapter (Evon)
│   │   ├── repositories/      # Deduplication persistence (SQLite)
│   │   ├── schemas/           # Pydantic schemas (Evidence, Intent, Voice)
│   │   └── services/          # AudioService (ffmpeg), Orchestrator
│   ├── data/                  # transcripts.csv manifest & audio clips
│   ├── scripts/               # test_gnani.py, eval_wer.py
│   └── tests/
│       ├── fixtures/          # Mock payloads
│       ├── live/              # Live integration smoke tests (skipped without keys)
│       └── unit/              # 16 unit tests (all passing)
├── evaluation/                # Evaluation datasets and results
└── frontend/                  # Next.js web demo (Phase 5)
```

---

## 3. Windows Setup & Quickstart

All commands must be executed in **Windows PowerShell**.

### Prerequisites
1. **Python 3.11+** (Detected: Python 3.13.3)
2. **Node.js LTS** (Detected: v22.16.0)
3. **FFmpeg & FFprobe**:
   ```powershell
   winget install Gyan.FFmpeg
   # Verify in a new terminal:
   ffmpeg -version
   ffprobe -version
   ```

### 1. Environment & Dependencies
```powershell
# Navigate to repository root
cd C:\Users\akhil\.gemini\antigravity\scratch\kisan-saathi

# Create and activate Python virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install backend dependencies
pip install -r backend/requirements-dev.txt
```

### 2. Environment Configuration
```powershell
# Copy template to backend/.env
Copy-Item .env.example backend\.env
# Open backend/.env and populate your GNANI_API_KEY and WHATSAPP_* secrets.
# (Do NOT commit real secret values to Git)
```

### 3. Verify Configuration & Run Tests
```powershell
# Run the test suite (16 unit tests mocked, live tests skipped without keys)
pytest backend/tests/

# Run code style and lint checks with ruff
ruff check backend/
```

### 4. Running the API Locally
```powershell
# Start Uvicorn development server
uvicorn backend.app.main:app --reload --port 8000
```
- Health Check: `http://localhost:8000/api/health`
- Interactive API Docs: `http://localhost:8000/docs`

### 5. Running the Gnani Smoke Test (LIVE)
Requires `GNANI_API_KEY` in `backend/.env`:
```powershell
# Test Telugu Text-to-Speech synthesis:
python -m backend.scripts.test_gnani --tts "నమస్కారం రైతు సోదరులారా" --lang te-IN

# Test Speech-to-Text transcription:
python -m backend.scripts.test_gnani --audio path\to\clip.wav --lang te-IN
```

### 6. Running the Speech Evaluation (WER / CER)
```powershell
python -m backend.scripts.eval_wer --csv backend/data/transcripts.csv
```

---

## 4. Current Project Status (Phase 0 & Phase 1 Complete)

| Component | Status | Verification State |
|---|---|---|
| Workspace & Git Initialization | ✅ Done | Initialized locally; secrets & media gitignored |
| Code Audit (`docs/code-audit.md`) | ✅ Done | All files audited; top 5 bugs documented |
| Core Typed Settings (`pydantic-settings`) | ✅ Done | Reads all `.env.example` keys; startup warning on pilot |
| Health Endpoint (`/api/health`) | ✅ Done | Exposes status & config booleans (never secret values) |
| Request-ID & Structured JSON Logging | ✅ Done | Salted phone hashes; no secrets or raw audio in logs |
| Gnani Prisma STT & Timbre TTS Adapters | ✅ Done | Explicit timeouts; 429/5xx retries; lang normalization |
| WhatsApp Webhook Hardening | ✅ Done | Production secret gate; constant-time sig; SQLite dedup |
| OpenAI-Compatible LLM Adapter | ✅ Done | Echo mode when unconfigured; disclosures attached |
| Audio Service (FFmpeg / FFprobe) | ✅ Done | 16kHz WAV conversion, OGG/Opus encoding, 25s chunking |
| Test Suite | ✅ Done | 16 passed, 2 skipped (LIVE without keys), 0 failed |

For the detailed living progress log and decisions, consult:
- [docs/PROGRESS.md](docs/PROGRESS.md)
- [docs/code-audit.md](docs/code-audit.md)
- [docs/MANUAL_TASKS.md](docs/MANUAL_TASKS.md)
- [docs/decisions.md](docs/decisions.md)
- [docs/PACK_README.md](docs/PACK_README.md)
