with open('backend/routes_data.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = """@router.get("/inventory/health", dependencies=[Depends(require_permission("view"))])
def inventory_health(page: int = 1, page_size: int = 10,
                     select_all: bool = False, q: Optional[str] = None, db: Session = Depends(get_db)):
    if hasattr(page_size, "default"):
        page_size = int(page_size.default)
    else:
        page_size = int(page_size) if page_size else 10
    if hasattr(page, "default"):
        page = int(page.default)
    else:
        page = int(page) if page else 1"""

replacement = """@router.get("/inventory/health", dependencies=[Depends(require_permission("view"))])
def inventory_health(page: int = 1, page_size: int = 10,
                     select_all: bool = False, q: Optional[str] = None, db: Session = Depends(get_db)):
    if hasattr(page, "query"):
        db = page
        page = 1
        page_size = 10
    else:
        if hasattr(page_size, "default"):
            page_size = int(page_size.default)
        else:
            page_size = int(page_size) if page_size else 10
        if hasattr(page, "default"):
            page = int(page.default)
        else:
            page = int(page) if page else 1"""

assert target in text, "Target not found in routes_data.py"
text = text.replace(target, replacement, 1)

with open('backend/routes_data.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated inventory_health to seamlessly support positional inventory_health(db)!")

