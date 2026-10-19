# Making CustomerVault live: Backend on Render, Frontend on Vercel, MySQL on Aiven

```
Browser -> Vercel  (frontend/: HTML, CSS, JS)
              |  calls  https://<your-backend>.onrender.com/api/...
              v
          Render   (backend/: FastAPI)  -> MySQL (Aiven, over TLS)
```
Render has no MySQL, so the database goes on Aiven (or any hosted MySQL: PlanetScale, Railway, a VPS...).
Do the steps in this order: **1 Database -> 2 Backend -> 3 Frontend -> 4 Connect them.**

## 0. Put the code on GitHub
Create a **private** repo and push the whole `my-website` folder (`.gitignore` already keeps `backend/.env` out - never push passwords).

## 1. Database (Aiven for MySQL)
1. Aiven console -> create a **MySQL** service, wait for *Running*.
2. Copy from the Overview page: Host, **Port** (the normal MySQL port, not "X Protocol"), User, Password, Database (default `defaultdb`).
3. Use `defaultdb` as the database name, or create your own: `CREATE DATABASE customer_database;` (the app does not create a database itself).
4. Allowed IPs: leave "open to all" (Render's IP changes), or add Render's outbound IPs.
5. **Copy your existing local database to Aiven** (your local data is only read, never changed). On your computer, in the project folder:

       pip install -r backend/requirements.txt
       python backend/migrate_to_aiven.py --check     (tests both connections)
       python backend/migrate_to_aiven.py             (copies every table and its rows)

   - The **source** is the login in `backend/.env` (your local MySQL, `customer_database`).
   - The **destination** is Aiven: the script asks for host, port, user, password and database (from Aiven -> Overview -> Connection information). Nothing is saved.
   - At the end it prints local rows vs Aiven rows for every table. Anything marked `CHECK` / `FAILED` must be fixed before going live (re-run with `--replace` to redo a table).
   - Use the same database name (`defaultdb`, or the one you created) as `MYSQL_DATABASE` on Render.
   - Alternative without the script: `mysqldump -u root -p --single-transaction --no-tablespaces customer_database > backup.sql`, then
     `mysql -h <HOST> -P <PORT> -u <USER> -p --ssl-mode=REQUIRED <DATABASE> < backup.sql`.

## 2. Backend on Render
1. render.com -> **New -> Blueprint** -> pick your repo (it reads `render.yaml`).
   *(Or New -> Web Service with: Runtime **Python 3**, Build `pip install -r backend/requirements.txt`, Start `python backend/main.py --host 0.0.0.0 --port $PORT --trust-proxy`.)*
2. Fill in the environment variables Render asks for:

       MYSQL_HOST      = <aiven host>
       MYSQL_PORT      = <aiven port>
       MYSQL_USER      = <user>
       MYSQL_PASSWORD  = <password>
       MYSQL_DATABASE  = <database>
       MYSQL_SSL       = true                (already set)
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
Change code -> `git push` -> Render and Vercel redeploy by themselves. Data stays in MySQL. Back up with `mysqldump` now and then.

## Troubleshooting
| Symptom | Cause / fix |
|---|---|
| "Cannot reach the server" on Vercel | Wrong `API_BASE`, or Render still waking up (wait 1 min) |
| Browser console: CORS error | `CORS_ORIGINS` on Render missing / has a trailing slash / wrong address |
| Render log: access denied / unknown database | Wrong `MYSQL_*` values; the database must already exist |
| Render log: connection refused / timed out | Wrong port (use the normal MySQL port) or Aiven IP allow-list |
| Render log: SSL / TLS error | Set `MYSQL_SSL=true` |
| Deleted customers come back | Set `CREATE_MISSING_CUSTOMER_TABLES=false` |
