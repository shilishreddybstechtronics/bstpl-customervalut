# Connection details checklist

Fill these in and keep the file PRIVATE. Real passwords go only into Render's Environment tab
or your local `backend/.env`, never into files that are pushed to GitHub.

## 1. TiDB Cloud (cluster -> Connect -> Connection Type: Public)
| Detail | Where to find it | Your value |
|---|---|---|
| Host | Connect dialog | `________` (like gateway01.<region>.prod.aws.tidbcloud.com) |
| Port | Connect dialog | `4000` |
| User | Connect dialog - the FULL name with prefix | `________` (like 2abc1234.root) |
| Password | Connect dialog -> Generate / Reset Password | `________` |
| Database | `test` exists by default (or create e.g. `cs`) | `test` |
| TLS | required | `MYSQL_SSL=true` |
| Public Endpoint | cluster -> Networking -> Enable | enabled? `____` |
| IP access list | Networking -> Add IP Address (0.0.0.0/0 for Render) | added? `____` |

## 2. Local MySQL (source of the copy)
| Detail | Your value |
|---|---|
| Host | `127.0.0.1` |
| Port | `3306` |
| User | `root` |
| Password | `________` |
| Database | `cs` |

## 3. Render (backend)
| Detail | Your value |
|---|---|
| Service name | `customervault-api` |
| Backend URL | `https://________.onrender.com` |

## 4. Vercel (frontend)
| Detail | Your value |
|---|---|
| Frontend URL | `https://________.vercel.app` |
| Root Directory | `frontend` |

## 5. Render environment variables
| Variable | Value |
|---|---|
| `MYSQL_HOST` | TiDB host |
| `MYSQL_PORT` | `4000` |
| `MYSQL_USER` | TiDB user (with prefix) |
| `MYSQL_PASSWORD` | TiDB password |
| `MYSQL_DATABASE` | `test` (or your database) |
| `MYSQL_SSL` | `true` |
| `PYTHON_VERSION` | `3.12.7` |
| `CORS_ORIGINS` | Vercel URL, no trailing slash |
