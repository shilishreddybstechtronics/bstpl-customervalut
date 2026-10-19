#!/usr/bin/env python3
"""migrate_to_aiven.py - copy your LOCAL MySQL database (tables + data) to Aiven (or any hosted MySQL).

  python backend/migrate_to_aiven.py --check      only test both connections
  python backend/migrate_to_aiven.py              copy everything (tables that already hold data on Aiven are skipped)
  python backend/migrate_to_aiven.py --replace    drop + re-copy tables that already exist on Aiven

SOURCE      = the login in backend/.env (your local MySQL: MYSQL_HOST / MYSQL_PORT / MYSQL_USER / MYSQL_PASSWORD / MYSQL_DATABASE).
DESTINATION = Aiven. Set DST_MYSQL_HOST / DST_MYSQL_PORT / DST_MYSQL_USER / DST_MYSQL_PASSWORD / DST_MYSQL_DATABASE as
              environment variables, or just run the script and type them (the password is not shown, nothing is saved).
              Optional: DST_MYSQL_SSL_CA = path to Aiven's ca.pem (verifies the certificate; otherwise the link is only encrypted).
Your local database is only READ - nothing is changed or deleted there.
"""
import getpass
import os
import ssl
import sys

import pymysql

import config   # also loads backend/.env

CHUNK = 1000


def q(name):
    return "`" + str(name).replace("`", "``") + "`"


def ask(env, label, default="", secret=False):
    v = os.environ.get(env)
    if v:
        return v
    if secret:
        return getpass.getpass(f"{label}: ")
    v = input(f"{label}" + (f" [{default}]" if default else "") + ": ").strip()
    return v or default


def connect(c, tls, ca=""):
    kw = dict(host=c["host"], port=int(c["port"]), user=c["user"], password=c["password"], database=c["database"],
              charset="utf8mb4", connect_timeout=20, read_timeout=600, write_timeout=600, autocommit=False)
    if tls:
        ctx = ssl.create_default_context(cafile=ca) if ca else ssl.create_default_context()
        if not ca:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        kw["ssl"] = ctx
    return pymysql.connect(**kw)


def base_tables(cur):
    cur.execute("SHOW FULL TABLES WHERE Table_type = 'BASE TABLE'")
    return [r[0] for r in cur.fetchall()]


def main():
    check = "--check" in sys.argv
    replace = "--replace" in sys.argv
    src = dict(config.MYSQL)
    print(f"SOURCE (local) : {src['user']}@{src['host']}:{src['port']}/{src['database']}")
    print("DESTINATION (Aiven) - enter the values from the Aiven console (Overview -> Connection information):")
    dst = {"host": ask("DST_MYSQL_HOST", "  host"), "port": ask("DST_MYSQL_PORT", "  port", "3306"),
           "user": ask("DST_MYSQL_USER", "  user", "avnadmin"), "password": ask("DST_MYSQL_PASSWORD", "  password", secret=True),
           "database": ask("DST_MYSQL_DATABASE", "  database", "defaultdb")}
    ca = os.environ.get("DST_MYSQL_SSL_CA", "").strip()
    if not dst["host"] or not dst["password"]:
        sys.exit("Host and password are required.")
    if (src["host"], int(src["port"]), src["database"]) == (dst["host"], int(dst["port"]), dst["database"]):
        sys.exit("Source and destination are the same database - stopping.")

    try:
        s = connect(src, tls=False)
    except Exception as e:
        sys.exit(f"Cannot connect to the LOCAL database: {e}\nIs MySQL running, and is backend/.env correct?")
    try:
        d = connect(dst, tls=True, ca=ca)
    except Exception as e:
        sys.exit(f"Cannot connect to Aiven: {e}\nCheck host / port (normal MySQL port, not X Protocol), user, password, database name, "
                 "and the service's allowed IP addresses.")
    sc, dc = s.cursor(), d.cursor()
    tables = base_tables(sc)
    print(f"\nConnected to both. Local database has {len(tables)} table(s).")
    if check:
        print("Connection test OK - nothing copied.")
        return
    if input(f"Copy them into '{dst['database']}' on {dst['host']}? (yes/no): ").strip().lower() != "yes":
        sys.exit("Cancelled.")

    for sql in ("SET SESSION foreign_key_checks = 0", "SET SESSION sql_mode = 'NO_AUTO_VALUE_ON_ZERO'",
                "SET SESSION sql_require_primary_key = 0"):   # Aiven can require a primary key; the last one may be refused - that is fine
        try:
            dc.execute(sql)
        except Exception:
            pass

    existing = set(base_tables(dc))
    done, skipped, failed = 0, [], []
    for t in tables:
        try:
            sc.execute(f"SELECT COUNT(*) FROM {q(t)}")
            total = sc.fetchone()[0]
            if t in existing:
                dc.execute(f"SELECT COUNT(*) FROM {q(t)}")
                have = dc.fetchone()[0]
                if replace:
                    dc.execute(f"DROP TABLE {q(t)}")
                elif have:
                    skipped.append(f"{t} ({have} rows already there)")
                    print(f"  skip   {t}")
                    continue
                else:
                    dc.execute(f"DROP TABLE {q(t)}")   # exists but empty: re-create exactly like the local one
            sc.execute(f"SHOW CREATE TABLE {q(t)}")
            dc.execute(sc.fetchone()[1])
            copied = 0
            if total:
                rc = s.cursor(pymysql.cursors.SSCursor)
                rc.execute(f"SELECT * FROM {q(t)}")
                cols = ", ".join(q(c[0]) for c in rc.description)
                ins = f"INSERT INTO {q(t)} ({cols}) VALUES ({', '.join(['%s'] * len(rc.description))})"
                while True:
                    rows = rc.fetchmany(CHUNK)
                    if not rows:
                        break
                    dc.executemany(ins, rows)
                    copied += len(rows)
                rc.close()
            d.commit()
            dc.execute(f"SELECT COUNT(*) FROM {q(t)}")
            got = dc.fetchone()[0]
            flag = "ok    " if got == total else "CHECK "
            print(f"  {flag} {t}: {total} row(s) local -> {got} on Aiven")
            if got != total:
                failed.append(f"{t}: {total} local vs {got} copied")
            done += 1
        except Exception as e:
            d.rollback()
            print(f"  FAILED {t}: {e}")
            failed.append(f"{t}: {e}")
    print(f"\nFinished: {done} table(s) copied, {len(skipped)} skipped, {len(failed)} problem(s).")
    for x in skipped:
        print("  skipped:", x)
    for x in failed:
        print("  PROBLEM:", x)
    if failed:
        print("Fix the problems above (or run again with --replace) before going live.")
    else:
        print(f"Done. Use MYSQL_DATABASE={dst['database']} in the Render environment variables.")


if __name__ == "__main__":
    main()
