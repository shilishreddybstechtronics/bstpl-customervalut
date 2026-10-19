# bstpl-customervalut (CustomerVault)

Frontend: plain HTML / CSS / JS (`frontend/`) | Backend: FastAPI (`backend/`) | Database: MySQL locally, TiDB Cloud online

```
my-website/
├── frontend/              -> deploy to Vercel (Root Directory = frontend)
│   ├── index.html, style.css, script.js, vercel.json
│   └── assets/            config.js (API address), extras.css, extras.js, logos
├── backend/               -> deploy to Render
│   ├── main.py            FastAPI app (API + serves the pages when run locally)
│   ├── database.py        MySQL code
│   ├── models.py, schemas.py, crud.py
│   ├── config.py, xlsxout.py, init_db.py, add_user.py
│   ├── migrate_to_tidb.py    copies your local MySQL database to TiDB Cloud
│   ├── requirements.txt
│   └── .env.example       copy to .env
├── render.yaml            Render blueprint
├── DEPLOYMENT.md          step-by-step: Render + Vercel + TiDB Cloud
├── CONNECTION_DETAILS.md  checklist of every value you must fill in
├── .gitignore
└── README.md
```

## Run locally (project root)
1. Start MySQL (your local database, e.g. `cs`, must exist).
2. `pip install -r backend/requirements.txt`
3. Create `backend/.env` from `backend/.env.example` (block A for local MySQL).
4. `python backend/main.py` -> open http://localhost:8000   (leave `API_BASE` empty in `frontend/assets/config.js`)
5. First admin: `python backend/add_user.py --admin` | database check: `python backend/init_db.py`

## Go live
See `DEPLOYMENT.md` and fill in `CONNECTION_DETAILS.md`.
