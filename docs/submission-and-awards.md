# Submission, Awards and Posting Plan

**Re-verify every item against the live challenge page before submitting** (https://www.gnani.ai/great-indian-ai-internship-registration-form). This file records what was understood on 1 Nov 2026.

## Understood requirements
- Deadline: 10 Nov 2026, no extensions. Internal target 9 Nov.
- Deliverables: working app, demo video, written explanation, public LinkedIn and/or X posts tagging Gnani with the required hashtags (#GnaniAI, #GreatIndianAIInternshipChallenge).
- Models: Prisma (STT), Timbre (TTS), Evon (LLM). 5,000 API credits per participant.
- Awards (reported: Rs 50,000 each; one person can win only one, verify): Regional Languages, Hinglish/Code-mixed, Noisy Telephonic Audio, Real-World Impact, Best Solo/Duo, Creativity, Tier 2/3 Towns, Best 60-second Demo, Crowd Favourite.
- Internship selection is separate from awards: it reportedly uses project review, post engagement and an interview. Awards do not change internship offers.
- No misleading demos, plagiarism, or paid/artificial engagement.

## How the project maps to awards
| Award | Evidence we will show |
|---|---|
| Regional languages | Telugu + Hindi voice loop, WER table per language |
| Hinglish / code-mixed | Hinglish test set, `indic-auto` vs explicit comparison |
| Noisy telephonic audio | E1 noise + telephone-simulation + WhatsApp-style results |
| Real-world impact | Farmers, real KCC + Agmarknet data, safety design |
| Best solo | Solo repo history, scope discipline, honest write-up |
| Creativity | Grounded voice agent with refusals and visible provenance |
| Tier 2/3 | Check if the rule goes by college or hometown (Jaipur is generally classed Tier 2) |
| 60-second demo | Script in `design.md` section 9 |
| Crowd Favourite | Relatable, shareable farmer story; real replies from real people |

## Posting plan (engagement counts up to the cutoff)
- **Tue 3 Nov evening:** teaser, 30 s clip of voice note in and voice note out.
- **Sat 7 Nov:** main demo video and write-up post (LinkedIn and X); tag Gnani, add hashtags.
- **Sun 8 and Mon 9 Nov:** short follow-ups (evaluation chart, behind-the-scenes, lessons).
- Ask classmates, family and farmer groups to look at it. Reply to every comment. Do not buy or trade engagement.

## Demo video (2 to 3 min) outline
Problem (15 s) -> WhatsApp voice note in Telugu, reply in voice with source (45 s) -> Hindi weather example (15 s) -> refusal of a dose question (15 s) -> web demo + dashboard (20 s) -> evaluation chart: clean vs noisy vs phone audio (30 s) -> architecture with the three Gnani models and limits (20 s). Show real latency; no scripted flawless run; mark synthetic data.

## Written explanation outline
1 Problem and users. 2 What it does (3 capabilities). 3 Architecture diagram and the role of Prisma, Evon, Timbre. 4 Data used (real vs synthetic). 5 Evaluation tables and error analysis. 6 Safety design. 7 Limits and honest caveats (which model answered, pilot region only, no PSTN yet). 8 What I would build next.

## Final checklist
- [ ] Public web demo URL works from a phone without login
- [ ] WhatsApp flow video recorded with a real phone
- [ ] README: setup, architecture, eval commands, data sources, licences
- [ ] No secrets or private audio in git history (rotate anything that leaked)
- [ ] Evaluation results reproducible from one command
- [ ] `LLM_DISCLOSED_NAME` accurate in all reported results
- [ ] Posts live with tags and hashtags; links saved
- [ ] Submission completed and confirmation screenshot saved
