import sys, os
sys.path.insert(0, os.path.abspath('backend'))
from database import SessionLocal
import models

db = SessionLocal()
try:
    blank_custs = db.query(models.Customer).filter((models.Customer.name == "") | (models.Customer.name == None)).all()
    print("Found blank customers:", len(blank_custs))
    for bc in blank_custs:
        db.delete(bc)
    db.commit()
    print("Cleaned up blank customers.")
finally:
    db.close()

