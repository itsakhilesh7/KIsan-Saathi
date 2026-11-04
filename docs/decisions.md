# Decision Log

Do not re-decide accepted items. Do not silently resolve pending ones: ask.

## What we took from the ChatGPT pack, and what we changed

**Kept (it is strong here):** evidence-first answers, the Evidence schema, tool allowlisting, LLM-never-selects-tools, strict Pydantic contracts, provenance rules, data-source status ladder, privacy defaults, completion-report discipline, `AGENTS.md` + Antigravity rule file, evaluation-metrics discipline.

**Changed, with reasons:**
| ChatGPT pack | This pack | Why |
|---|---|---|
| Web-only MVP; WhatsApp deferred | **WhatsApp primary, web demo secondary** | WhatsApp is the user's stated requirement and the best fit for Tier 2/3, noisy-audio and Crowd Favourite awards. The web demo stays because judges cannot message the Meta test number. |
| Telugu-first only | Telugu + Hindi + English, Hinglish tested | The developer speaks all three; broadens regional and code-mixed award fit |
| Crop advisory from 5 hand-picked ICAR/KVK docs | **Real KCC Q&A records** (+ a few curated docs) | Uses a large real dataset; a stronger real-data story; less manual curation |
| Pilot region/crops "pending, agent must not decide" | **Proposed defaults in `config/pilot.example.yaml`**, verified on Day 1 | A 10-day solo build cannot wait on open questions |
| Evon self-hosting out of scope | Evon preferred via an OpenAI-compatible adapter; stand-in allowed; **mandatory disclosure** | Shows all three Gnani models without risking the build, and stays honest |
| Prisma v2.5 default | **Prisma v3.0** (`indic-auto`) | v3.0 adds language auto-detect, which matters for code-mixed speech |
| Citing an unverified `gnani-vachana` SDK | REST adapters built from verified docs | Fewer unknowns |
| 7 phases without dates; no engagement plan | **Dated Nov 1 to Nov 10 plan**, teaser/main post dates, cut-lines | The deadline is hard and post engagement counts toward shortlisting |
| Frontend-heavy (5 pages) | Minimal single-page web demo | Solo capacity |
| Supabase for everything | Supabase for events/eval; vectors in pgvector or FAISS; **hosted embeddings at query time** | Free hosting tiers cannot hold a large embedding model |
| No evaluation depth | Evaluation is a deliverable: WER by noise/telephony condition, retrieval vs none, slot F1, refusal suite | This is the strongest evidence for awards and the internship |

## Decisions

| ID | Decision | Status | Notes |
|---|---|---|---|
| D-001 | Source-grounded agricultural voice assistant; not a general chatbot | Accepted | |
| D-002 | Channels: WhatsApp (primary) + web demo (secondary) | Accepted | WhatsApp primary target; Telegram fallback ACTIVE for development due to Meta test account locking (error 131031). WhatsApp remains target channel if account unlocked/replaced. |
| D-003 | STT: Prisma v3.0 over REST, `indic-auto` + explicit language | Accepted | Verify Telugu/Hinglish quality (Phase 0/1) |
| D-004 | TTS: Timbre v2.5 default; compare v3.0 for Telugu | Accepted | Choose by listening tests |
| D-005 | Capabilities: mandi, weather, KCC-grounded crop Q&A | Accepted | |
| D-006 | Backend: FastAPI layered structure; migrate `existing-code/` | Accepted | Keep existing tests passing |
| D-007 | Chemical doses suppressed by default (`ALLOW_CHEMICAL_DETAILS=false`) | Accepted | Revisit only with reviewed sources |
| D-008 | Embeddings: hosted API at query time, offline index build | **Pending** | Recommend a hosted multilingual embedding API; test Telugu retrieval on 30 queries first |
| D-009 | LLM hosting for Evon | **Pending** | Order: Gnani-hosted if it exists (ask Discord) -> rented GPU with vLLM/SGLang -> stand-in model with disclosure |
| D-010 | Pilot region and crops | **Pending confirmation** | Default in `config/pilot.example.yaml`; confirm on Day 1 against live data |
| D-011 | Audio retention | Proposed | 24 h default (`AUDIO_RETENTION_HOURS`); delete after processing in demo |
| D-012 | Deployment hosts | **Pending** | API: Render/Railway/Fly; web: Vercel; DB: Supabase |
| D-013 | PSTN calling / WhatsApp Calling API | Deferred | Stretch: browser click-to-call only if all exit criteria pass |
| D-014 | Hindi pilot B (Rajasthan/Jaipur) | Deferred | Enable after Phase 4 |
