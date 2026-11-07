# Kisan Saathi Deployment Guide

This guide details how to deploy Kisan Saathi as a hosted public service on **Render** (recommended) or **Railway**, configure the Telegram webhook mode, protect your Gnani credits with usage caps, and manage runtime behavior.

---

## 1. Hosting Recommendation: Render vs Railway

| Feature | Render (Recommended) | Railway |
|---|---|---|
| **Free / Starter Tier** | Generous Web Service with auto-HTTPS | Usage-based credits ($5/month credit) |
| **Docker Support** | First-class native `Dockerfile` support | Native Docker support |
| **Healthchecks** | Built-in zero-downtime healthcheck on `/health` | Supported via service settings |
| **Public URL** | `https://<service-name>.onrender.com` | `https://<service-name>.up.railway.app` |
| **Verdict** | **Recommended** for simplicity, clean HTTPS endpoints, and reliable Telegram webhooks. | Excellent alternative if you already maintain a Railway project. |

---

## 2. Prerequisites & Environment Variables

Configure the following environment variables in your deployment dashboard (Render: **Environment** tab; Railway: **Variables** tab).

### Core & Secrets
| Variable | Description | Example / Default |
|---|---|---|
| `APP_ENV` | Application environment mode | `production` |
| `PHONE_HASH_SALT` | Secret salt for irreversibly hashing phone/user IDs | `your_long_random_salt_here` |
| `FRONTEND_ORIGIN` | Allowed CORS origin (or `*`) | `*` |

### Telegram Integration (Webhook Mode)
| Variable | Description | Example / Default |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Token provided by `@BotFather` | `123456789:ABCdefGHI...` |
| `TELEGRAM_WEBHOOK_PATH` | Random secret URL path segment | `w7k9_webhook_a1b2c3d4` |
| `TELEGRAM_WEBHOOK_SECRET` | Secret token verified via `X-Telegram-Bot-Api-Secret-Token` | `secr3t_token_xyz890` |

> [!TIP]
> Generate secure random tokens with Python:
> ```bash
> python -c "import secrets; print(secrets.token_urlsafe(16))"
> ```

### Speech & Data Providers
| Variable | Description | Example / Default |
|---|---|---|
| `GNANI_API_KEY` | API key for Gnani Prisma STT and Timbre TTS | *(Required for voice)* |
| `DATA_GOV_API_KEY` | API key for data.gov.in Agmarknet mandi prices | *(Required for live mandi)* |
| `MANDI_RESOURCE_ID` | Agmarknet commodity arrivals resource ID | `9ef84268-d588-465a-a308-a864a43d0070` |
| `OPEN_METEO_BASE_URL` | Open-Meteo forecast endpoint | `https://api.open-meteo.com/v1/forecast` |

### Usage Caps & Abuse Prevention
| Variable | Description | Default |
|---|---|---|
| `DAILY_USER_VOICE_LIMIT` | Maximum voice queries per user per day | `10` |
| `DAILY_GLOBAL_VOICE_LIMIT` | Global circuit breaker for voice queries per day | `200` |
| `PUBLIC_VOICE_MAX_SECONDS` | Rejection cutoff for inbound voice notes | `30` |
| `ADMIN_USER_HASHES` | Comma-separated hashed user IDs exempt from limits | `hash1,hash2` |

---

## 3. Deployment Steps on Render

1. **Create Web Service**:
   - Log in to [dashboard.render.com](https://dashboard.render.com/).
   - Click **New +** $\rightarrow$ **Web Service**.
   - Connect your GitHub repository (`kisan-saathi`).
2. **Runtime Settings**:
   - **Environment**: `Docker`
   - **Region**: Singapore (`singapore`) or nearest to India for minimal latency to data.gov.in and Gnani.
   - **Branch**: `main`
   - **Plan**: Free or Starter
3. **Health Check Path**:
   - Set **Health Check Path** to `/health`.
4. **Start Command**:
   - Dockerfile default: `uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}`
5. **Add Environment Variables**:
   - Paste all required environment variables listed in Section 2.
6. **Deploy**:
   - Click **Create Web Service**. Wait for build and health check to pass.
   - Note your public service URL: `https://<service-name>.onrender.com`.

---

## 4. Setting Up the Telegram Webhook

Once your web service is live and `/health` returns `{"status":"healthy"}`:

1. In your local terminal where `.env` contains your `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_PATH`, and `TELEGRAM_WEBHOOK_SECRET`, run:
   ```bash
   python -m backend.scripts.manage_telegram_webhook set https://<service-name>.onrender.com
   ```
2. Verify that Telegram successfully registered the endpoint:
   ```bash
   python -m backend.scripts.manage_telegram_webhook info
   ```
3. Test your bot directly in Telegram by sending a greeting or asking for a crop price (e.g., "పత్తి ధర ఎంత?").

### Returning to Local Development (Polling Mode)
To test locally without webhook forwarding:
```bash
python -m backend.scripts.manage_telegram_webhook delete
python -m backend.scripts.run_telegram_polling
```

---

## 5. Storage Architecture & Ephemeral Filesystems Note

> [!IMPORTANT]
> **Ephemeral Disk Notice**:
> Render and Railway free/starter containers use ephemeral disks.
> Whenever a new deployment is triggered or the container restarts:
> - SQLite database files in `data/*.sqlite3` (`user_preferences.sqlite3`, `usage_limits.sqlite3`, `deduplication.sqlite3`, `mandi_cache.sqlite3`) will reset.
> - **Self-Healing Design**:
>   - The Mandi cache is warmed asynchronously in the background on startup (`fetch_mandi_prices` runs non-blocking).
>   - Deduplication will start fresh for new update IDs.
>   - Daily voice counters reset on restart.
> 
> If persistent state across redeploys is required for production, attach a **Persistent Disk** mounted at `/app/data` in Render/Railway service settings.
