# Sensorise SenseLCM Integration - BSTPL CustomerVault

This directory houses the complete Sensorise SenseLCM telematics subsystem, data files, dynamic SenseCrypt authentication engine, FastAPI proxy routes, and TiDB Cloud database persistence.

## 📂 Subsystem Structure & Files
```
backend/sensorise/
├── .env                           # Live active credentials, database & auth tokens
├── .env.example                   # Environment template
├── config.py                      # Production SenseLCM URLs, DB configs & file paths
├── sensorise.py                   # SenseCrypt HMAC-SHA512 auth & SenseLCM REST engine
├── db.py                          # TiDB / MySQL persistence & sensorise_sims_basic schema
├── main.py                        # FastAPI microservice endpoints (24 routes)
├── app_logger.py                  # Diagnostic file logging & root cause analysis
├── requirements.txt               # Dependencies (fastapi, uvicorn, pymysql, pandas, etc.)
├── Sensorise_SIMs_basic.xlsx      # Master basic SIM dataset (25,056 devices)
├── Sensorise_SIMs_basic_updated.xlsx # Verified telematics records (80 devices)
├── telematics_cache.json          # Cached genuine Sensorise server telematics
└── README.md                      # Subsystem documentation
```

---

## 🌐 1. Sensorise Production Server Endpoints & Links
- **Base URL**: `https://senselcm.sensorise.net/sense-lcm-services-prod`
- **Check SIM Bulk V2**: `https://senselcm.sensorise.net/sense-lcm-services-prod/checkSIMBulk/v2/`
- **Generate API Token**: `https://senselcm.sensorise.net/sense-lcm-services-prod/generateAPIToken`
- **CustomerVault API Docs (Swagger)**: `http://127.0.0.1:8000/docs#/Sensorise`
- **Local Health & Diagnostics**: `http://127.0.0.1:8000/api/sensorise/status`

---

## 🔑 2. Authentication & Token Lifecycle (SenseCrypt)
- **Relation ID**: `SENSE1019`
- **Algorithm**: SenseCrypt Dynamic HMAC-SHA512
- **Seed**: `YYYYMMDD` (current date in UTC/IST)
- **Token Validity**: 24 Hours
- **Quota**: 100 Transactions per Token
- **Token Expiry Variable**: `SENSORISE_TOKEN_EXPIRY`
- **Token Refresh**: Triggered on-demand via Settings Pop-up Modal or `POST /api/sensorise/generate-token`. When refreshed, it automatically updates `.env` and in-memory caches.

---

## 💾 3. Database Persistence (`sensorise_sims_basic`)
- **Database Engine**: TiDB Cloud MySQL 8.0 Compatible (`gateway01.ap-northeast-1.prod.aws.tidbcloud.com:4000`)
- **Database Name**: `customer_database`
- **Table**: `sensorise_sims_basic`
- **Columns**: `id`, `device_sr_no`, `imei`, `iccid`, `msisdn1`, `msisdn2`, `activation_date`, `expiry_date`, `created_at`
- **Live Sync Flow**: When devices are requested via `/api/devices`, `/api/fetch/bulk`, or `/api/fetch/sync`, missing/updated SIMs are queried from Sensorise's server using ICCID; `msisdn1`, `msisdn2`, `activation_date`, and `expiry_date` are replaced with fresh server values in both the database and website response.

---

## 🖥️ 4. Frontend Settings Pop-up Modal
- Accessible via the **Settings** page (`frontend/settings.html`).
- Features a quick-action button in the user profile header and a dedicated **Sensorise SenseLCM Gateway** card.
- Opens the **Sensorise SenseLCM Gateway Hub** dialog modal (`#dlgSensoriseHub`) featuring:
  - Official corporate BSTPL logo badge.
  - Live server status indicator with ping test.
  - Live Token Expiration timestamp and real-time countdown badge.
  - Interactive "Generate Fresh Token" button with SenseCrypt HMAC-SHA512 generation.
  - Direct 1-click copyable links to all official endpoints and Swagger API documentation.
  - Database telematics summary with link to Fetch Data.
