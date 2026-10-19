# bstpl-customervalut (CustomerVault)

Frontend: plain HTML / CSS / JS (`frontend/`) | Backend: FastAPI (`backend/`) | Database: MySQL

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
│   ├── migrate_to_aiven.py   copies your local MySQL database to Aiven
│   ├── requirements.txt
│   └── .env.example       copy to .env (local MySQL login)
├── render.yaml            Render blueprint
├── DEPLOYMENT.md          step-by-step: Render + Vercel + Aiven MySQL
├── .gitignore
└── README.md
```

## Run locally (project root)
1. Start MySQL (database `customer_database` must exist).
2. `pip install -r backend/requirements.txt`
3. Check `backend/.env` (default: root / 1234 / customer_database).
4. `python backend/main.py` -> open http://localhost:8000   (leave `API_BASE` empty in `frontend/assets/config.js`)
5. First admin: `python backend/add_user.py --admin` | database check: `python backend/init_db.py`

## Go live
See `DEPLOYMENT.md`.
