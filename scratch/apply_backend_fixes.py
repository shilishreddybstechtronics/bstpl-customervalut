import re

# 1. Update backend/routes_customers.py to add GET /{cid}
with open('backend/routes_customers.py', 'r', encoding='utf-8') as f:
    text_c = f.read()

get_cid_route = '''@router.get("/{cid}", dependencies=[Depends(require_permission("view"))])
def get_customer(cid: int, db: Session = Depends(get_db)):
    c = db.query(Customer).filter(Customer.id == cid, Customer.deleted_at.is_(None)).first()
    if not c:
        raise HTTPException(404, "Customer not found")
    soon = date.today() + timedelta(days=30)
    dev_count = db.query(func.count(Device.id)).filter(Device.customer_id == c.id, Device.deleted_at.is_(None)).scalar() or 0
    exp_count = db.query(func.count(Device.id)).filter(Device.customer_id == c.id, Device.deleted_at.is_(None), Device.expiry_date <= soon).scalar() or 0
    return {
        "id": c.id,
        "name": c.name,
        "avatar": c.avatar,
        "devices": dev_count,
        "expiring_or_expired": int(exp_count)
    }


'''

if '@router.get("/{cid}"' not in text_c:
    pos = text_c.find('@router.put("/{cid}/avatar"')
    if pos != -1:
        text_c = text_c[:pos] + get_cid_route + text_c[pos:]
        with open('backend/routes_customers.py', 'w', encoding='utf-8') as f:
            f.write(text_c)
        print("Added GET /{cid} to routes_customers.py")
    else:
        print("WARNING: Could not find @router.put('/{cid}/avatar') in routes_customers.py")
else:
    print("GET /{cid} already in routes_customers.py")

# 2. Update backend/routes_data.py add_customer validation
with open('backend/routes_data.py', 'r', encoding='utf-8') as f:
    text_d = f.read()

old_add = '''@router.post("/customers", status_code=201, dependencies=[Depends(require_permission("add"))])
def add_customer(data: schemas.CustomerIn, db: Session = Depends(get_db),
                 user: models.User = Depends(get_current_user)):
    c = customer_by_name(db, data.name.strip())'''

new_add = '''@router.post("/customers", status_code=201, dependencies=[Depends(require_permission("add"))])
def add_customer(data: schemas.CustomerIn, db: Session = Depends(get_db),
                 user: models.User = Depends(get_current_user)):
    cname = (data.name or "").strip()
    if not cname:
        raise HTTPException(400, "Customer name cannot be blank.")
    if len(cname) > 150 or re.search(r"[;\\`\\'\\"]", cname):
        raise HTTPException(400, "Customer name contains invalid characters or exceeds 150 characters.")
    c = customer_by_name(db, cname)'''

if old_add in text_d:
    text_d = text_d.replace(old_add, new_add, 1)
    with open('backend/routes_data.py', 'w', encoding='utf-8') as f:
        f.write(text_d)
    print("Updated add_customer in routes_data.py with blank validation")
else:
    # Try CRLF
    old_add_crlf = old_add.replace('\n', '\r\n')
    new_add_crlf = new_add.replace('\n', '\r\n')
    if old_add_crlf in text_d:
        text_d = text_d.replace(old_add_crlf, new_add_crlf, 1)
        with open('backend/routes_data.py', 'w', encoding='utf-8') as f:
            f.write(text_d)
        print("Updated add_customer in routes_data.py (CRLF)")
    else:
        print("WARNING: Could not find old_add in routes_data.py")

