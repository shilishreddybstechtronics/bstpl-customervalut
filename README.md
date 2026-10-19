# bstpl-customervalut (CustomerVault)

```
my-website/
├── frontend/
│   ├── index.html
│   ├── style.css
│   ├── script.js
│   └── assets/            extras.css, extras.js, logos (xlsx.full.min.js optional offline copy)
├── backend/
│   ├── main.py            web server + API routes
│   ├── database.py        MySQL connection + all database logic
│   ├── models.py          table / column layout (reference)
│   ├── schemas.py         error types returned by the API
│   ├── crud.py            list of the record / customer / user operations
│   ├── requirements.txt
│   ├── .env.example       copy to .env and enter your MySQL login
│   └── config.py, xlsxout.py, init_db.py, add_user.py   (helpers used by the app)
├── .gitignore
└── README.md
```

## Run locally (from the project root)
1. Install Python 3.10+ and start MySQL.
2. `pip install -r backend/requirements.txt`
3. Copy `backend/.env.example` to `backend/.env` and put your MySQL password in it
   (the zip already contains a local `.env`: root / 1234 / customer_database - edit if yours differs).
4. `python backend/main.py` then open http://localhost:8000
5. Check the database: `python backend/init_db.py`  |  create an admin login: `python backend/add_user.py --admin`

## Front-end notes
The UI keeps the original HTML structure, JavaScript behaviour, API routes and database logic, with improved
visual hierarchy, spacing, responsive layout, keyboard focus visibility, table readability and reduced-motion support.
