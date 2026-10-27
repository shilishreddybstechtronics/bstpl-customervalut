"""Customer management: rename, bulk rename, merge, delete to the bin, restore.
Roles: admin + standard can rename, merge and restore. Only an admin can delete a customer or delete one for good."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

import customer_tables
import models, schemas
from activity import log_activity
from auth import get_current_user, require_admin, require_staff, require_permission
from database import get_db

router = APIRouter(prefix="/api/customers", dependencies=[Depends(get_current_user)])
Customer, Device = models.Customer, models.Device
TAG = "Customer deleted: "  # devices that went to the bin WITH their customer carry this reason


def active_customer(db: Session, cid: int) -> Customer:
    c = db.get(Customer, cid)
    if not c or c.deleted_at:
        raise HTTPException(404, "Customer not found.")
    return c


def name_taken(db: Session, name: str, ignore_ids=()) -> bool:
    q = db.query(Customer.id).filter(func.lower(Customer.name) == name.lower())
    if ignore_ids:
        q = q.filter(Customer.id.notin_(list(ignore_ids)))
    return q.first() is not None


ALLOWED_IMG = ("data:image/jpeg;base64,", "data:image/png;base64,", "data:image/webp;base64,")


@router.put("/{cid}/avatar", dependencies=[Depends(require_permission("edit"))])
def set_avatar(cid: int, data: schemas.AvatarIn, db: Session = Depends(get_db),
               user: models.User = Depends(get_current_user)):
    c = active_customer(db, cid)
    a = (data.avatar or "").strip()
    if a and not a.startswith(ALLOWED_IMG) and len(a) > 16:
        raise HTTPException(400, "Choose an emoji or upload a JPG, PNG or WebP picture.")
    c.avatar = a or None
    log_activity(db, "customer_icon", f"{c.name}: icon {'changed' if a else 'removed'}", user=user)
    db.commit()
    return {"id": c.id, "avatar": c.avatar}


@router.patch("/{cid}", dependencies=[Depends(require_staff), Depends(require_permission("edit"))])
def rename(cid: int, data: schemas.CustomerRename, db: Session = Depends(get_db),
           user: models.User = Depends(get_current_user)):
    import re
    c = active_customer(db, cid)
    raw = data.name.strip()
    new = re.sub(r"[^a-zA-Z0-9_]+", "_", raw).strip("_") or raw
    if not new:
        raise HTTPException(400, "Please enter a valid customer name.")
    if name_taken(db, new, ignore_ids=(cid,)):
        raise HTTPException(400, "Another customer already has this name (it may be in Deleted Customers).")
    old, c.name = c.name, new
    log_activity(db, "customer_rename", f"{old} -> {new}", user=user)
    db.commit()
    try:
        customer_tables.rename_table(c.id, new, old)
    except Exception as e:
        print(f"Customer table rename failed: {e}")
    return {"id": c.id, "name": c.name}


@router.post("/rename-all", dependencies=[Depends(require_staff), Depends(require_permission("edit"))])
def rename_all(data: schemas.RenameAllIn, db: Session = Depends(get_db),
               user: models.User = Depends(get_current_user)):
    """All-or-nothing. Swaps (A->B and B->A in one go) work too."""
    wanted = {}
    for item in data.renames:
        if item.id in wanted:
            raise HTTPException(400, "The same customer appears twice.")
        wanted[item.id] = item.name.strip()
    if any(not n for n in wanted.values()):
        raise HTTPException(400, "A new name cannot be empty.")
    lowered = [n.lower() for n in wanted.values()]
    if len(set(lowered)) != len(lowered):
        raise HTTPException(400, "Two customers would end up with the same name.")
    customers = {c.id: c for c in db.query(Customer).filter(Customer.id.in_(list(wanted)))}
    changed = []
    for cid, new in wanted.items():
        c = customers.get(cid)
        if not c or c.deleted_at:
            raise HTTPException(404, "A customer in the list was not found.")
        if c.name != new:
            changed.append((c, new))
    if not changed:
        return {"renamed": 0}
    changing_ids = [c.id for c, _ in changed]
    for c, new in changed:  # clash with a customer that is NOT part of this rename
        if name_taken(db, new, ignore_ids=changing_ids):
            raise HTTPException(400, f'The name "{new}" is already used by another customer.')
    for c, _ in changed:  # step 1: temporary names, so swaps never hit the unique constraint
        c.name = f"__renaming_{c.id}"
    db.flush()
    for c, new in changed:
        c.name = new
    log_activity(db, "customer_rename_all", f"{len(changed)} customers renamed", user=user)
    db.commit()
    for c, new in changed:
        try:
            customer_tables.rename_table(c.id, new)
        except Exception as e:
            print(f"Customer table rename failed: {e}")
    return {"renamed": len(changed)}


@router.post("/{cid}/merge", dependencies=[Depends(require_staff), Depends(require_permission("edit"))])
def merge(cid: int, data: schemas.MergeIn, db: Session = Depends(get_db),
          user: models.User = Depends(get_current_user)):
    """Moves every device (bin included) from this customer into the target, syncs customer tables, then removes this customer."""
    target_id = getattr(data, "target_id", None) or getattr(data, "target_customer_id", None)
    if not target_id or cid == target_id:
        raise HTTPException(400, "Choose a different customer to merge into.")
    src, dst = active_customer(db, cid), active_customer(db, target_id)

    # 1. Update customer_id for all devices (active and bin)
    moved = db.query(Device).filter(Device.customer_id == src.id).update(
        {"customer_id": dst.id},
        synchronize_session=False
    )

    # 2. Update delete_reason if any devices were deleted with src
    db.query(Device).filter(
        Device.customer_id == dst.id,
        Device.delete_reason == f"{TAG}{src.name}"
    ).update(
        {"delete_reason": f"{TAG}{dst.name}"},
        synchronize_session=False
    )

    # 3. Update any ErroredRecords referencing src.name to dst.name
    db.query(models.ErroredRecord).filter(
        models.ErroredRecord.customer_name == src.name
    ).update(
        {"customer_name": dst.name},
        synchronize_session=False
    )

    # 4. Remove src customer from customers table
    src_name = src.name
    dst_name = dst.name
    src_id = src.id
    dst_id = dst.id

    db.delete(src)
    log_activity(db, "customer_merge", f"{src_name} merged into {dst_name} ({moved} records moved)", user=user)
    db.commit()

    # 5. Merge dedicated SQL/TiDB Cloud customer tables
    try:
        customer_tables.merge_tables(src_id, src_name, dst_id, dst_name)
    except Exception as me:
        print(f"Customer table merge notice: {me}")

    # 6. Mirror all active devices of dst to ensure dst customer table is completely synchronized
    try:
        devs = db.query(Device).filter(Device.customer_id == dst_id, Device.deleted_at.is_(None)).all()
        mirror_items = []
        for d in devs:
            mirror_items.append((dst_id, dst_name, {
                "imei": d.imei, "customer_name": dst_name, "device_sr_no": d.device_sr_no,
                "iccid": d.iccid, "msisdn1": d.msisdn1, "msisdn2": d.msisdn2,
                "act_date": d.act_date, "expiry_date": d.expiry_date, "dispatched_date": d.dispatched_date,
                "model": d.model, "sim_provider": d.sim_provider, "activation_plan": d.activation_plan,
                "firmware": d.firmware, "flash": d.flash, "sim_type": d.sim_type,
                "extra": d.extra or {}
            }))
        if mirror_items:
            customer_tables.mirror_rows(mirror_items)
    except Exception as me:
        print(f"Customer table mirror notice after merge: {me}")

    return {"moved": moved, "into": dst_name}


@router.delete("/{cid}", dependencies=[Depends(require_admin), Depends(require_permission("delete"))])
def delete_customer(cid: int, db: Session = Depends(get_db), admin: models.User = Depends(require_admin)):
    c = active_customer(db, cid)
    now = datetime.utcnow()
    n = (db.query(Device).filter(Device.customer_id == c.id, Device.deleted_at.is_(None))
         .update({"deleted_at": now, "deleted_by": admin.user_id, "delete_reason": TAG + c.name},
                 synchronize_session=False))  # one UPDATE instead of one per device
    c.deleted_at, c.deleted_by = now, admin.user_id
    log_activity(db, "customer_delete", f"{c.name} moved to bin ({n} records)", user=admin)
    db.commit()
    return {"moved_to_bin": c.id, "devices": n}


# ---------- deleted customers ----------
@router.get("/bin", dependencies=[Depends(require_staff), Depends(require_permission("view"))])
def bin_customers(db: Session = Depends(get_db)):
    rows = (db.query(Customer, func.count(Device.id))
            .outerjoin(Device, Device.customer_id == Customer.id)
            .filter(Customer.deleted_at.isnot(None))
            .group_by(Customer.id).order_by(Customer.deleted_at.desc()).all())
    return [{"id": c.id, "name": c.name, "devices": n, "deleted_at": c.deleted_at, "deleted_by": c.deleted_by}
            for c, n in rows]


@router.post("/{cid}/restore", dependencies=[Depends(require_staff), Depends(require_permission("edit"))])
def restore_customer(cid: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    c = db.get(Customer, cid)
    if not c or not c.deleted_at:
        raise HTTPException(404, "Not in the bin.")
    # bring back the devices that were deleted together with the customer, not ones deleted earlier on their own
    n = (db.query(Device).filter(Device.customer_id == c.id, Device.deleted_at.isnot(None),
                                 Device.delete_reason.like(TAG + "%"))
         .update({"deleted_at": None, "deleted_by": None, "delete_reason": None}, synchronize_session=False))
    c.deleted_at = c.deleted_by = None
    log_activity(db, "customer_restore", f"{c.name} restored ({n} records)", user=user)
    db.commit()
    return {"restored": c.id, "devices": n}


@router.delete("/{cid}/purge", dependencies=[Depends(require_admin), Depends(require_permission("delete"))])
def purge_customer(cid: int, db: Session = Depends(get_db), admin: models.User = Depends(require_admin)):
    c = db.get(Customer, cid)
    if not c or not c.deleted_at:
        raise HTTPException(404, "Not in the bin.")
    c_name = c.name
    n = db.query(Device).filter(Device.customer_id == c.id).delete(synchronize_session=False)
    log_activity(db, "customer_purge", f"{c.name} deleted forever ({n} records)", user=admin)
    db.delete(c)
    db.commit()
    try:
        customer_tables.drop_table(cid, c_name)
    except Exception as e:
        print(f"Customer table drop failed: {e}")
    return {"purged": cid, "devices": n}
