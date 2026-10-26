# CustomerVault - Vercel Deployment Guide

Your project is configured to deploy directly to **Vercel** with full FastAPI backend and static frontend support.

---

## 🚀 How to Deploy on Vercel (Step-by-Step)

### Step 1: Push Your Code to GitHub
Ensure all new files (`vercel.json`, `api/index.py`, `.python-version`, etc.) are pushed:
```bash
git add .
git commit -m "Configure Vercel deployment with Python 3.12 and TiDB integration"
git push origin main
```

---

### Step 2: Import into Vercel
1. Go to [vercel.com](https://vercel.com) and log in.
2. Click **"Add New..."** → **"Project"**.
3. Select your GitHub repository: `bstpl-customervalut`.
4. **Project Settings**:
   - **Framework Preset**: Other / None (leave default)
   - **Root Directory**: `./` (leave default root, do NOT change to backend)
   - **Build Command**: leave empty (Vercel automatically detects Python 3.12 and dependencies)
   - **Output Directory**: leave empty

---

### Step 3: Add Environment Variables in Vercel (Optional but Recommended)
Under **Environment Variables**, you can add your TiDB Cloud credentials:

| Key | Value |
|---|---|
| `DB_HOST` | `gateway01.ap-northeast-1.prod.aws.tidbcloud.com` |
| `DB_PORT` | `4000` |
| `DB_USER` | `2qvzCb4ckY28YTR.root` |
| `DB_PASSWORD` | `TkUlyIt79g9JLww0` |
| `DB_NAME` | `customer_database` |
| `DB_SSL` | `true` |
| `SECRET_KEY` | `60bab0872e7d08bd77521ed0576eb3be17e16a33b4e1865cb27e3cd86b1be43c` |

*(Note: We have also embedded safe production fallbacks directly in `database.py`, so even if an environment variable is omitted, it will automatically connect to your TiDB Cloud database!)*

---

### Step 4: Click Deploy!
Vercel will:
1. Build Python 3.12 dependencies with `uv`.
2. Deploy the FastAPI API Serverless Function under `api/index.py`.
3. Deploy the static dashboard and index HTML under `frontend/`.
4. Route `/api/*`, `/auth/*`, `/health/*` directly to FastAPI.

---

## 🔗 Connecting Vercel Frontend to Render Backend (Alternative)
If you prefer running your backend on Render (`https://bstpl-customervalut-20.onrender.com`) and your frontend on Vercel:
1. On your Vercel website, click the **`⚙️ Set Server URL`** button right next to the database status.
2. Enter:
   ```text
   https://bstpl-customervalut-20.onrender.com
   ```
3. Click OK. Your website will instantly connect to your Render backend and turn green!
