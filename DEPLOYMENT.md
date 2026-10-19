# Making CustomerVault live: Backend on Render, Frontend on Vercel, MySQL on TiDB Cloud

```
Browser -> Vercel  (frontend/: HTML, CSS, JS)
              |  calls  https://<your-backend>.onrender.com/api/...
              v
          Render   (backend/: FastAPI)  -> TiDB Cloud (MySQL compatible, over TLS)
```
Render has no MySQL, so the database goes on TiDB Cloud (MySQL compatible). It cannot reach the MySQL on your own computer.
Do the steps in this order: **1 Database -> 2 Backend -> 3 Frontend -> 4 Connect them.**

## 0. Put the code on GitHub
Create a **private** repo and push the whole `my-website` folder (`.gitignore` already keeps `backend/.env` out - never push passwords).

## 1. Database (TiDB Cloud)
1. TiDB Cloud console -> open your cluster -> **Networking**: click **Enable** for the Public Endpoint, then **Add IP Address** and allow `0.0.0.0/0` (Render's IP changes).
2. Click **Connect** (top right), choose connection type **Public**, and copy: Host, **Port** (`4000`), **User** (the full name with prefix, e.g. `2abc1234.root`), Password (generate or reset it there), Database (`test` by default).
3. Use `test` as the database name, or create your own in the SQL Editor: `CREATE DATABASE cs;` (the app does not create a database itself).
4. TiDB Cloud requires a secure connection, so `MYSQL_SSL=true` is always needed. No CA file is required.
5. **Copy your existing local database to TiDB** (your local data is only read, never changed). On your computer, in the project folder:

       pip install -r backend/requirements.txt
       python backend/init_db.py                      (local check - fix any PROBLEM line first)
       python backend/migrate_to_tidb.py --check      (tests both connections)
       python backend/migrate_to_tidb.py              (copies every table and its rows)

   - The **source** is the login in `backend/.env`: your LOCAL MySQL (host 127.0.0.1, port 3306, your local database). Do this step before putting TiDB values in `.env`.
   - The **destination** is TiDB: the script asks for host, port, user, password and database. Nothing is saved.
   - At the end it prints local rows vs TiDB rows for every table. Anything marked `CHECK` / `FAILED` must be fixed before going live (re-run with `--replace` to redo a table).
   - Use the same database name as `MYSQL_DATABASE` on Render.
   - Alternative without the script: `mysqldump -u root -p --single-transaction --no-tablespaces cs > backup.sql`, then
     `mysql -h <HOST> -P 4000 -u <PREFIX.root> -p --ssl-mode=REQUIRED <DATABASE> < backup.sql`.

## 2. Backend on Render
1. render.com -> **New -> Blueprint** -> pick your repo (it reads `render.yaml`).
   *(Or New -> Web Service with: Runtime **Python 3**, Root Directory **empty**, Build `pip install -r backend/requirements.txt`, Start `python backend/main.py --host 0.0.0.0 --port $PORT --trust-proxy`.
   If you set Root Directory = `backend` instead, use Build `pip install -r requirements.txt` and Start `python main.py --host 0.0.0.0 --port $PORT --trust-proxy`. Always end with `$PORT`, never a number.)*
2. Fill in the environment variables Render asks for:

       MYSQL_HOST      = <tidb host>         (Connect dialog -> Host)
       MYSQL_PORT      = 4000
       MYSQL_USER      = <prefix>.root       (the full name)
       MYSQL_PASSWORD  = <password>
       MYSQL_DATABASE  = test              (or the database you created)
       MYSQL_SSL       = true                (already set)
       PYTHON_VERSION  = 3.12.7              (already set)
       CORS_ORIGINS    = https://<your-site>.vercel.app    (fill in after step 3; no trailing slash)

3. Deploy. Open `https://<name>.onrender.com/` - you should see the login page. **Copy this URL.**
4. Your logins were copied with the database, so you can log in with your existing accounts. To create an extra admin (on your own computer, same variables as above):

       set MYSQL_HOST=...  set MYSQL_PORT=...  set MYSQL_USER=...  set MYSQL_PASSWORD=...  set MYSQL_DATABASE=...  set MYSQL_SSL=true      (Windows)
       python backend/add_user.py --admin                                                                                                   (use export instead of set on Mac/Linux)

5. After the first good start set `CREATE_MISSING_CUSTOMER_TABLES=false` on Render. Otherwise every restart re-creates customers you deleted, because `backend/config.py` still lists them.
6. Free plan note: Render's free service sleeps after ~15 min idle; the first visit then takes about a minute. Use a paid plan for real use.

## 3. Frontend on Vercel
1. Open `frontend/assets/config.js` and set your Render URL (no trailing slash):

       window.API_BASE = 'https://<name>.onrender.com';

   Commit and push.
2. vercel.com -> **Add New -> Project** -> import the repo.
3. Settings: **Root Directory = `frontend`**, Framework Preset = **Other**, Build Command = empty, Output Directory = empty (or `.`).
4. Deploy. You get `https://<your-site>.vercel.app`.

## 4. Connect them
1. Go back to Render -> your service -> Environment -> set `CORS_ORIGINS=https://<your-site>.vercel.app`
   (several addresses: comma separated, e.g. `https://a.vercel.app,https://vault.mycompany.com`). Save - Render redeploys.
2. Open the Vercel address, log in, add a record, search, download Excel.
   If the page says it cannot reach the server: check `API_BASE` in `config.js`, `CORS_ORIGINS` on Render, and that Render has finished waking up.

## 5. Your own domain (optional)
- Frontend: Vercel -> Project -> Settings -> Domains -> add `vault.yourcompany.com`, then create the DNS record Vercel shows.
- Backend: Render -> Settings -> Custom Domains (e.g. `api.yourcompany.com`); then update `API_BASE` and add the new frontend domain to `CORS_ORIGINS`.
- HTTPS certificates are automatic on both.

## 6. Before real users
- Change the sample password `1234` and use a strong MySQL password.
- The admin IDs `0001`, `0002`, `0003`, `1234` in `backend/config.py` (ROLES) are guessable - create admins with strong passwords and change those IDs.
- Keep the repo private. Never commit `.env`.

## 7. Updating later
Change code -> `git push` -> Render and Vercel redeploy by themselves. Data stays in MySQL. Back up with `mysqldump` now and then (TiDB Cloud also has its own backups).

## Troubleshooting
| Symptom | Cause / fix |
|---|---|
| "Cannot reach the server" on Vercel | Wrong `API_BASE`, or Render still waking up (wait 1 min) |
| Browser console: CORS error | `CORS_ORIGINS` on Render missing / has a trailing slash / wrong address |
| Render log: `root@127.0.0.1:3306/customer_database` | The `MYSQL_*` variables are not set on this Render service - add them in Environment, then **Save, rebuild and deploy** |
| Render log: access denied | Wrong password, or the user name lacks its prefix (use the full `<prefix>.root`) |
| Render log: unknown database | `MYSQL_DATABASE` must exist on TiDB (`test`, or run `CREATE DATABASE cs;`) |
| Render log: connection refused / timed out | Wrong port (use `4000`), Public Endpoint not enabled, or your IP is not in the TiDB IP access list |
| Render log: SSL / TLS error or "requires secure connection" | Set `MYSQL_SSL=true` |
| `Exited with status 127` / `status 2` | Wrong Build/Start command or Root Directory (see step 2.1) |
| Deleted customers come back | Set `CREATE_MISSING_CUSTOMER_TABLES=false` |
