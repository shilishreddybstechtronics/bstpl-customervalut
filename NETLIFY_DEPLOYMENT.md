# CustomerVault - Netlify Deployment Guide

Your project is configured for **1-click instant deployment on Netlify**.

Because your backend is live on Render (`https://bstpl-customervalut-2-jm3t.onrender.com`), Netlify will host the frontend and automatically proxy all database/auth/API requests with zero CORS issues.

---

## 🚀 How to Deploy on Netlify (Step-by-Step)

### Step 1: Log in to Netlify
1. Go to **[app.netlify.com](https://app.netlify.com/)** and sign in (using GitHub).

### Step 2: Import Your Repository
1. Click **"Add new site"** → **"Import an existing project"**.
2. Select **GitHub**.
3. Choose the repository: **`bstpl-customervalut`** (or `shilishreddybstechtronics/bstpl-customervalut`).

### Step 3: Site Configuration
Netlify will automatically detect [`netlify.toml`](file:///c:/Users/soumy/OneDrive/Documents/hhhhhhhhh/netlify.toml), but verify:
- **Base directory**: Leave empty (root)
- **Build command**: Leave empty
- **Publish directory**: `frontend`

*(You do **not** need to set any environment variables in Netlify, because the database is hosted on TiDB Cloud via Render!)*

### Step 4: Click "Deploy bstpl-customervalut"
- Netlify will finish deploying in under 10 seconds.
- You will receive a URL like: `https://<random-name>.netlify.app`.

---

## 🔒 Verification
1. Open your Netlify URL.
2. The header will show: **`Database online and verified ⚙️`**.
3. You can log in, add customers, edit columns, and manage files immediately.
