# CustomerVault - Render Deployment Guide

Your project folders and files have been prepared and configured for **Render** deployment.

---

## 📁 What Has Been Prepared

1. **`render.yaml` (Blueprint)**: 1-click deployment configuration for Render.
2. **`Procfile`** (both root and `backend/`): Standard web process specification (`web: uvicorn main:app --host 0.0.0.0 --port $PORT`).
3. **`requirements.txt`** (both root and `backend/`): Dependencies pinned with production ASGI server (`uvicorn[standard]` & `gunicorn`).
4. **`.python-version`**: Pinned to Python `3.12` (supported by both Vercel and Render).
5. **`.gitignore`**: Protects your secret keys and local `.env` files from being pushed to public repositories.
6. **Dynamic Host & Port Binding**: Both `backend/main.py` and root `main.py` read `$PORT` and bind to `0.0.0.0`.
7. **Production CORS Support**: Seamless communication between backend on Render and any frontend domain.
8. **Cloud Database Support**: `database.py` safely supports both individual `DB_*` variables and unified `DATABASE_URL`.

---

## 🚀 How to Deploy on Render

### Step 1: Push your code to GitHub / GitLab
Make sure your project is pushed to a repository on GitHub or GitLab:
```bash
git init
git add .
git commit -m "Prepare folders and configuration for Render deployment"
git branch -M main
git remote add origin <YOUR_GITHUB_REPO_URL>
git push -u origin main
```
*(Notice: `.gitignore` protects your local `.env` file so your passwords will not be committed to GitHub).*

---

### Step 2: Deploy on Render

You can choose either of the two methods below:

#### Option A: Using Render Blueprints (Recommended - 1-Click)
1. Go to [dashboard.render.com](https://dashboard.render.com).
2. Click **New +** -> **Blueprint**.
3. Select your GitHub repository.
4. Render will read `render.yaml` automatically and configure:
   - **Name**: `customervault`
   - **Runtime**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Fill in the database environment variables when prompted (see table below).
6. Click **Apply**.

---

#### Option B: Manual Web Service Setup
1. Go to [dashboard.render.com](https://dashboard.render.com).
2. Click **New +** -> **Web Service**.
3. Connect your GitHub repository.
4. Fill in the service details:
   - **Name**: `customervault-backend` (or your choice)
   - **Region**: Choose the region closest to your database (e.g., *Singapore / Oregon / Frankfurt*)
   - **Branch**: `main`
   - **Root Directory**: Leave blank (or `backend` if you want backend only)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt` *(or `pip install -r backend/requirements.txt`)*
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: `Free` or higher

---

### Step 3: Add Environment Variables in Render

In your Render Web Service dashboard, go to the **Environment** tab and add the following keys:

| Key | Value | Description |
|---|---|---|
| `DB_HOST` | `gateway01.ap-northeast-1.prod.aws.tidbcloud.com` | TiDB Cloud Host |
| `DB_PORT` | `4000` | Port |
| `DB_USER` | `2qvzCb4ckY28YTR.root` | TiDB Username |
| `DB_PASSWORD` | `<your-tidb-password>` | TiDB Password |
| `DB_NAME` | `customer_database` | Database Name |
| `DB_SSL` | `true` | Required for TiDB Cloud |
| `SECRET_KEY` | *(Click "Generate" on Render or paste 64 hex characters)* | JWT Token Security |
| `TRUST_PROXY` | `true` | Allows reading real client IP behind Render |

*(Optional)* If hosting your frontend on a separate domain (e.g., Vercel, Netlify):
- `ALLOWED_ORIGINS`: `https://my-frontend.vercel.app` (or leave empty to allow all)

---

## 🌐 Serving Frontend & Backend

### 1. Unified (Default & Simplest)
Because FastAPI is configured to serve the `frontend/` directory, Render serves **BOTH** your frontend and backend on the same URL:
- Opening `https://bstpl-customervalut-2-jm3t.onrender.com/` opens the dashboard.
- Opening `https://bstpl-customervalut-2-jm3t.onrender.com/health/db` checks the database health.
- Opening `https://bstpl-customervalut-2-jm3t.onrender.com/docs` opens the Swagger API documentation.

### 2. Frontend Hosted Separately
If you prefer to host `frontend/` on Netlify, Vercel, or GitHub Pages:
- In `frontend/index.html` (or in browser console):
  `localStorage.setItem('API_URL', 'https://bstpl-customervalut-2-jm3t.onrender.com')`
- The backend's CORS is pre-configured to accept requests from your external frontend!
