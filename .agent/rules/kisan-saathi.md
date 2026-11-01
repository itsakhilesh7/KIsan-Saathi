---
trigger: always_on
description: Kisan Saathi project rules. Full details live in AGENTS.md and rules.md.
---

- Read `AGENTS.md`, then `rules.md` and the active phase in `phases.md` before changing code.
- WhatsApp is the primary channel; a web demo is the secondary channel. No PSTN/telephony without an explicit phase change.
- Use only the Gnani endpoints documented in `docs/gnani-api-notes.md`. Never invent parameters.
- Every market, weather or crop fact must come from a retrieved tool result or approved document. Never invent numbers, dates, sources, diagnoses or chemical doses.
- Secrets stay on the backend. The frontend never calls providers directly.
- Distinguish live-verified integrations from mocked tests in every report.
- Plan first for multi-file work; implement only the active phase.
