# Experiment E1: Robustness of Prisma STT v3.0

**Evaluation Conditions & Ground Truth Invariants:**
- Mode: `explicit` language code (`te-IN` for Telugu, `hi-IN` for Hindi/Hinglish).
- Identical string normalizer applied to references and hypotheses (`normalize_text`).
- Hinglish Roman reference strings evaluated via intent extraction (`extract_intent`), not WER.

| Language | Condition | n | Mean WER | Mean CER | Intent Acc |
|---|---|---|---|---|---|
| **Hindi** | `clean` | 4 | **12.68%** | ** 6.21%** | - |
| **Hindi** | `noise_pink_snr20` | 4 | **13.93%** | ** 5.92%** | - |
| **Hindi** | `noise_pink_snr10` | 4 | **15.18%** | ** 6.50%** | - |
| **Hindi** | `noise_pink_snr5` | 4 | **19.28%** | **10.44%** | - |
| **Hindi** | `noise_brown_snr20` | 4 | **15.18%** | ** 7.66%** | - |
| **Hindi** | `noise_brown_snr10` | 4 | **12.68%** | ** 5.92%** | - |
| **Hindi** | `noise_brown_snr5` | 4 | **13.93%** | ** 7.37%** | - |
| **Hindi** | `tel_g711` | 4 | **15.18%** | ** 6.50%** | - |
| **Hindi** | `tel_amrnb` | 4 | **15.24%** | ** 7.10%** | - |
| **Hindi** | `whatsapp_opus` | 4 | **11.43%** | ** 5.92%** | - |
| **Hinglish** | `clean` | 2 | N/A | N/A | ** 50.0%** |
| **Hinglish** | `noise_pink_snr10` | 2 | N/A | N/A | ** 50.0%** |
| **Hinglish** | `tel_g711` | 2 | N/A | N/A | ** 50.0%** |
| **Telugu** | `clean` | 4 | **12.40%** | ** 3.89%** | - |
| **Telugu** | `noise_pink_snr20` | 4 | **14.32%** | ** 3.24%** | - |
| **Telugu** | `noise_pink_snr10` | 4 | **14.32%** | ** 4.54%** | - |
| **Telugu** | `noise_pink_snr5` | 4 | **16.59%** | ** 4.87%** | - |
| **Telugu** | `noise_brown_snr20` | 4 | **12.40%** | ** 3.57%** | - |
| **Telugu** | `noise_brown_snr10` | 4 | **14.32%** | ** 3.24%** | - |
| **Telugu** | `noise_brown_snr5` | 4 | **12.40%** | ** 3.89%** | - |
| **Telugu** | `tel_g711` | 4 | **16.59%** | ** 4.87%** | - |
| **Telugu** | `tel_amrnb` | 4 | **14.32%** | ** 4.54%** | - |
| **Telugu** | `whatsapp_opus` | 4 | **14.32%** | ** 4.54%** | - |