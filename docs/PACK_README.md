# Kisan Saathi: Agent Pack (final)

Planning and instruction pack for building **Kisan Saathi**, a WhatsApp-first voice assistant for farmers, with Codex or Google Antigravity. It merges a ChatGPT-generated pack with our own verified findings and a working starter codebase. It is documentation, not an application.

## Contents
| File | Purpose |
|---|---|
| `AGENTS.md` | Instructions both Codex and Antigravity read automatically |
| `.agents/rules/` and `.agent/rules/` | Antigravity workspace rule (always on); both folder names are included because Antigravity docs differ by version |
| `prd.md` | What we build, acceptance criteria, risks |
| `architecture.md` | Stack, pipeline, repo layout, contracts, retrieval design |
| `rules.md` | Invariants: evidence, agricultural safety, security, code, agent workflow |
| `phases.md` | Dated plan, 1 to 10 Nov 2026, with cut-lines |
| `design.md` | Web demo, WhatsApp content rules, demo script |
| `docs/decisions.md` | Decisions and what changed vs the ChatGPT pack |
| `docs/gnani-api-notes.md` | Verified Prisma/Timbre/Evon facts and unverified items |
| `docs/whatsapp-integration.md` | Meta Cloud API specifics and limits |
| `docs/data-sources.md` | Mandi, weather, KCC, speech datasets, status register |
| `docs/evaluation-plan.md` | E1 to E6 experiments and reporting rules |
| `docs/submission-and-awards.md` | Requirements, award mapping, posting plan, checklist |
| `docs/prompts/` | Kickoff prompt, phase prompts, review prompts |
| `config/pilot.example.yaml` | Proposed pilot region/crops (verify Day 1) |
| `evaluation/` | Case manifest example and results folder |
| `.env.example`, `.gitignore` | Variable names only; blocks secrets and audio |

## Setup
1. Create a new folder/repo and extract **this pack** into its root.
2. Extract the separate **`kisan-saathi.zip`** (the starter code) into a subfolder named `existing-code/`.
3. `git init`, copy `.env.example` to `backend/.env` (fill locally; never commit), copy `config/pilot.example.yaml` to `config/pilot.yaml`.
4. Open the repo root in Antigravity (or Codex).
5. Open `docs/prompts/00-kickoff.md`, choose a model (below), and paste the prompt. Review the audit and plan before approving implementation.

## Which model to use
- **Claude Opus:** kickoff audit and plan, retrieval/safety design (P4), hard debugging.
- **Claude Sonnet:** day-to-day implementation. Best default for most tasks.
- **Gemini Flash:** cheap, fast work: boilerplate, test scaffolding, docs, data-cleaning scripts, UI polish.
- **GPT/Codex:** independent reviewer. Use `docs/prompts/02-review-prompts.md`.
Availability and quotas depend on your plan; if Opus is limited, spend it on the kickoff and P4 only.

## Working rules of thumb
- One phase at a time; review each report; commit after each phase.
- Do the manual tasks yourself (keys, Meta dashboard, recordings, GPU rental, posts). The agent cannot.
- Never paste API keys into an agent chat; rotate any key that leaks.
- If time slips, cut from the bottom of the priority list in `phases.md`.
