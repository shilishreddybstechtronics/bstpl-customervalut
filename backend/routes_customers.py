"""
================================================================================
BSTPL Customer Vault - Enterprise Customer Management Router
File: backend/routes_customers.py
================================================================================
Architectural Overview:
-----------------------
This router manages the complete lifecycle of customer organizations in the
BSTPL Customer Vault telematics platform.

Key Engineering Design Principles Implemented:
1. Dual-Tier Soft Deletion (Recycling Bin):
   - Rather than irrevocably destroying records on customer deletion, entities
     and their linked telemetry devices are stamped with `deleted_at` and `deleted_by`.
   - Preserves complete operational audit history and allows instant restoration.

2. Route Shadowing Prevention (FastAPI Greedy Route Order):
   - Static subpaths (e.g. `/api/customers/bin`) MUST be registered before dynamic
     parameterized routes (e.g. `/api/customers/{cid}`).
   - If `/{cid: int}` is evaluated first, FastAPI attempts to cast `"bin"` to `int`,
     producing an unhandled HTTP 422 Unprocessable Content error.

3. Atomic Multi-Customer Renaming with Collision Bypass:
   - Circular renames (Customer A -> B and Customer B -> A) are executed via a
     two-phase swap using temporary placeholders (`__renaming_{cid}`) to prevent
     SQL UNIQUE constraint violations.

4. Dynamic Physical Table Synchronization:
   - When customers are created, renamed, merged, or purged, this module triggers
     cascading DDL/DML actions in `backend/customer_tables.py` to keep dedicated
     per-customer SQL tables (`c<id>_<name>`) in sync with the unified master catalog.

5. High-Performance Batch Mutations:
   - Massive updates and deletions use SQLAlchemy's `synchronize_session=False`
     to execute directly at the database engine level, achieving O(1) memory
     overhead even when thousands of devices are affected.
================================================================================
"""

import re
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

import customer_tables
import models
import schemas
from activity import log_activity
from auth import get_current_user, require_admin, require_staff, require_permission
from database import get_db

# Initialize API router with universal Bearer token authentication
router = APIRouter(
    prefix="/api/customers",
    tags=["Customers"],
    dependencies=[Depends(get_current_user)]
)

# Aliases for clean ORM queries
Customer = models.Customer
Device = models.Device

# Audit tracking tag applied to devices soft-deleted together with their customer organization
CUSTOMER_DELETED_TAG = "Customer deleted: "

# Whitelist of accepted Base64 data URI image formats for customer avatars
ACCEPTED_IMAGE_MIME_PREFIXES = (
    "data:image/jpeg;base64,",
    "data:image/png;base64,",
    "data:image/webp;base64,"
)


# ==============================================================================
# SECTION 1: INTERNAL HELPER UTILITIES & QUERY GUARDS
# ==============================================================================

def get_active_customer_or_404(db: Session, customer_id: int) -> Customer:
    """
    Retrieves an active (non-deleted) customer by primary key ID.

    Args:
        db: Active SQLAlchemy database session.
        customer_id: Integer primary key of the customer.

    Returns:
        Customer: The verified active customer model.

    Raises:
        HTTPException(404): If customer does not exist or has been moved to the bin.
    """
    customer = db.get(Customer, customer_id)
    if not customer or customer.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Active customer with ID {customer_id} was not found."
        )
    return customer


def is_customer_name_taken(db: Session, candidate_name: str, excluded_ids: tuple = ()) -> bool:
    """
    Checks case-insensitively whether a customer name is already registered,
    optionally ignoring specific customer IDs (useful during self-renames or merges).

    Args:
        db: Active SQLAlchemy database session.
        candidate_name: Desired customer organization name.
        excluded_ids: Tuple of customer IDs to exclude from collision checking.

    Returns:
        bool: True if name is already occupied in active or bin records, False otherwise.
    """
    query = db.query(Customer.id).filter(
        func.lower(Customer.name) == candidate_name.strip().lower()
    )
    if excluded_ids:
        query = query.filter(Customer.id.notin_(list(excluded_ids)))
    return query.first() is not None


# Backwards compatibility alias for internal imports
active_customer = get_active_customer_or_404
name_taken = is_customer_name_taken


# ==============================================================================
# SECTION 2: CUSTOMER QUERIES & RETRIEVAL ENDPOINTS
# ==============================================================================

# NOTE: /bin MUST remain physically registered ABOVE /{cid} to prevent route collision!
@router.get(
    "/bin",
    summary="List soft-deleted customers in recycling bin",
    dependencies=[Depends(require_staff), Depends(require_permission("view"))]
)
def list_deleted_customers(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """
    Retrieves all soft-deleted customers currently residing in the recycling bin,
    along with their device counts and deletion audit timestamps.
    """
    deleted_records = (
        db.query(Customer, func.count(Device.id))
        .outerjoin(Device, Device.customer_id == Customer.id)
        .filter(Customer.deleted_at.isnot(None))
        .group_by(Customer.id)
        .order_by(Customer.deleted_at.desc())
        .all()
    )

    return [
        {
            "id": cust.id,
            "name": cust.name,
            "devices": device_count,
            "deleted_at": cust.deleted_at,
            "deleted_by": cust.deleted_by
        }
        for cust, device_count in deleted_records
    ]


# Alias for backward compatibility
bin_customers = list_deleted_customers


@router.get(
    "/{cid}",
    summary="Get single customer details and inventory health metrics",
    dependencies=[Depends(require_permission("view"))]
)
def get_customer_details(cid: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Fetches customer profile by ID, computing live device counts and upcoming
    30-day SIM/warranty expiration counts for proactive client management.
    """
    customer = (
        db.query(Customer)
        .filter(Customer.id == cid, Customer.deleted_at.is_(None))
        .first()
    )
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID {cid} was not found."
        )

    # Compute expiration window threshold (today through next 30 days)
    thirty_day_threshold = date.today() + timedelta(days=30)

    # Fast scalar aggregations for inventory status counts
    total_active_devices = (
        db.query(func.count(Device.id))
        .filter(Device.customer_id == customer.id, Device.deleted_at.is_(None))
        .scalar() or 0
    )

    expiring_soon_devices = (
        db.query(func.count(Device.id))
        .filter(
            Device.customer_id == customer.id,
            Device.deleted_at.is_(None),
            Device.expiry_date <= thirty_day_threshold
        )
        .scalar() or 0
    )

    return {
        "id": customer.id,
        "name": customer.name,
        "avatar": customer.avatar,
        "devices": int(total_active_devices),
        "expiring_or_expired": int(expiring_soon_devices)
    }


# Alias for backward compatibility
get_customer = get_customer_details


# ==============================================================================
# SECTION 3: CUSTOMER PROFILE & METADATA MUTATIONS
# ==============================================================================

@router.put(
    "/{cid}/avatar",
    summary="Update or remove customer avatar icon",
    dependencies=[Depends(require_permission("edit"))]
)
def set_customer_avatar(
    cid: int,
    data: schemas.AvatarIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Updates a customer's visual avatar using either an emoji glyph or a compact
    Base64-encoded image string (JPG, PNG, WebP).
    """
    customer = get_active_customer_or_404(db, cid)
    avatar_payload = (data.avatar or "").strip()

    # Validate image payload format: emoji (< 16 chars) or legitimate Base64 URI
    if avatar_payload:
        is_legit_image = avatar_payload.startswith(ACCEPTED_IMAGE_MIME_PREFIXES)
        if not is_legit_image and len(avatar_payload) > 16:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Avatar must be a valid emoji character or a Base64 JPG/PNG/WebP image string."
            )

    customer.avatar = avatar_payload if avatar_payload else None
    action_label = "updated" if avatar_payload else "removed"
    log_activity(
        db,
        action="customer_icon",
        detail=f"{customer.name}: Avatar icon {action_label}",
        user=current_user
    )
    db.commit()

    return {"id": customer.id, "avatar": customer.avatar}


# Alias for backward compatibility
set_avatar = set_customer_avatar


@router.patch(
    "/{cid}",
    summary="Rename single customer and synchronize dedicated table",
    dependencies=[Depends(require_staff), Depends(require_permission("edit"))]
)
def rename_customer(
    cid: int,
    data: schemas.CustomerRename,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Renames a customer, validating uniqueness, logging the audit record,
    and renaming the dedicated physical table (`c<id>_<old>` -> `c<id>_<new>`).
    """
    customer = get_active_customer_or_404(db, cid)
    raw_name = data.name.strip()

    # Sanitize name to SQL-safe alphanumeric + underscores
    sanitized_name = re.sub(r"[^a-zA-Z0-9_]+", "_", raw_name).strip("_") or raw_name
    if not sanitized_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer name cannot be empty or solely special characters."
        )

    # Collision check excluding current customer ID
    if is_customer_name_taken(db, sanitized_name, excluded_ids=(cid,)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Another customer named "{sanitized_name}" already exists (or is in the recycling bin).'
        )

    previous_name = customer.name
    customer.name = sanitized_name
    log_activity(
        db,
        action="customer_rename",
        detail=f'Renamed customer: "{previous_name}" -> "{sanitized_name}"',
        user=current_user
    )
    db.commit()

    # Synchronize physical table in TiDB/SQLite
    try:
        customer_tables.rename_table(customer.id, sanitized_name, previous_name)
    except Exception as table_err:
        print(f"[Customer Table Rename Warning] Could not rename physical SQL table: {table_err}")

    return {"id": customer.id, "name": customer.name}


# Alias for backward compatibility
rename = rename_customer


@router.post(
    "/rename-all",
    summary="Atomic bulk rename with collision-free circular swap support",
    dependencies=[Depends(require_staff), Depends(require_permission("edit"))]
)
def bulk_rename_customers(
    data: schemas.RenameAllIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Performs an all-or-nothing atomic batch rename across multiple customers.
    
    Technical Highlights:
    - Pre-validates duplicate names across inputs and database records.
    - Uses a two-phase swap with temporary placeholders (`__renaming_{id}`)
      so circular swaps (e.g. Customer A -> B and Customer B -> A) never trip
      the SQL unique constraint.
    """
    desired_renames: Dict[int, str] = {}
    for item in data.renames:
        if item.id in desired_renames:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Customer ID {item.id} appears multiple times in rename payload."
            )
        desired_renames[item.id] = item.name.strip()

    if any(not name for name in desired_renames.values()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A new customer name cannot be blank."
        )

    # Check for duplicate names inside the payload itself
    lowered_names = [name.lower() for name in desired_renames.values()]
    if len(set(lowered_names)) != len(lowered_names):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Two or more customers would end up with the exact same name."
        )

    # Fetch matching customers from database
    existing_customers = {
        c.id: c
        for c in db.query(Customer).filter(Customer.id.in_(list(desired_renames.keys())))
    }

    pending_changes = []
    for cid, new_name in desired_renames.items():
        customer = existing_customers.get(cid)
        if not customer or customer.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer ID {cid} was not found or is currently in the recycling bin."
            )
        if customer.name != new_name:
            pending_changes.append((customer, new_name))

    if not pending_changes:
        return {"renamed": 0}

    # Verify no collisions with external customer records outside this batch
    batch_customer_ids = [c.id for c, _ in pending_changes]
    for customer, new_name in pending_changes:
        if is_customer_name_taken(db, new_name, excluded_ids=tuple(batch_customer_ids)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'The requested name "{new_name}" is already taken by another customer.'
            )

    # PHASE 1: Assign temporary non-colliding names to avoid SQL unique constraint violations during swaps
    for customer, _ in pending_changes:
        customer.name = f"__renaming_{customer.id}"
    db.flush()

    # PHASE 2: Apply desired final names
    for customer, final_name in pending_changes:
        customer.name = final_name

    log_activity(
        db,
        action="customer_rename_all",
        detail=f"Bulk renamed {len(pending_changes)} customer organizations.",
        user=current_user
    )
    db.commit()

    # PHASE 3: Synchronize physical SQL tables in TiDB/SQLite
    for customer, final_name in pending_changes:
        try:
            customer_tables.rename_table(customer.id, final_name)
        except Exception as table_err:
            print(f"[Bulk Table Rename Warning] Table rename failed for ID {customer.id}: {table_err}")

    return {"renamed": len(pending_changes)}


# Alias for backward compatibility
rename_all = bulk_rename_customers


# ==============================================================================
# SECTION 4: CUSTOMER MERGING & CONSOLIDATION
# ==============================================================================

@router.post(
    "/{cid}/merge",
    summary="Merge source customer into destination customer and consolidate inventory",
    dependencies=[Depends(require_staff), Depends(require_permission("edit"))]
)
def merge_customers(
    cid: int,
    data: schemas.MergeIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Consolidates two customer entities:
    1. Reassigns all active and binned devices from source to destination.
    2. Updates deletion reasons and quarantine error records referencing source.
    3. Deletes source customer entity.
    4. Merges physical SQL customer tables and ensures complete synchronization.
    """
    target_id = getattr(data, "target_id", None) or getattr(data, "target_customer_id", None)
    if not target_id or cid == target_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please specify a valid, distinct destination customer to merge into."
        )

    source_cust = get_active_customer_or_404(db, cid)
    dest_cust = get_active_customer_or_404(db, target_id)

    # Step 1: Reassign all hardware devices (both active and in the bin)
    moved_devices_count = (
        db.query(Device)
        .filter(Device.customer_id == source_cust.id)
        .update({"customer_id": dest_cust.id}, synchronize_session=False)
    )

    # Step 2: Update delete audit reason tag if any devices were binned with source
    db.query(Device).filter(
        Device.customer_id == dest_cust.id,
        Device.delete_reason == f"{CUSTOMER_DELETED_TAG}{source_cust.name}"
    ).update(
        {"delete_reason": f"{CUSTOMER_DELETED_TAG}{dest_cust.name}"},
        synchronize_session=False
    )

    # Step 3: Reassign any quarantined errored records referencing source customer name
    db.query(models.ErroredRecord).filter(
        models.ErroredRecord.customer_name == source_cust.name
    ).update(
        {"customer_name": dest_cust.name},
        synchronize_session=False
    )

    # Capture metadata before removing source customer row
    source_name, dest_name = source_cust.name, dest_cust.name
    source_id, dest_id = source_cust.id, dest_cust.id

    # Step 4: Remove source customer from master customers table
    db.delete(source_cust)
    log_activity(
        db,
        action="customer_merge",
        detail=f'Merged "{source_name}" into "{dest_name}" ({moved_devices_count} devices reassigned).',
        user=current_user
    )
    db.commit()

    # Step 5: Merge physical SQL/TiDB Cloud customer tables
    try:
        customer_tables.merge_tables(source_id, source_name, dest_id, dest_name)
    except Exception as merge_err:
        print(f"[Customer Table Merge Notice] {merge_err}")

    # Step 6: Verify and mirror active devices into destination table
    try:
        active_dest_devices = (
            db.query(Device)
            .filter(Device.customer_id == dest_id, Device.deleted_at.is_(None))
            .all()
        )
        mirror_payload = [
            (dest_id, dest_name, {
                "imei": dev.imei,
                "customer_name": dest_name,
                "device_sr_no": dev.device_sr_no,
                "iccid": dev.iccid,
                "msisdn1": dev.msisdn1,
                "msisdn2": dev.msisdn2,
                "act_date": dev.act_date,
                "expiry_date": dev.expiry_date,
                "dispatched_date": dev.dispatched_date,
                "model": dev.model,
                "sim_provider": dev.sim_provider,
                "activation_plan": dev.activation_plan,
                "firmware": dev.firmware,
                "flash": dev.flash,
                "sim_type": dev.sim_type,
                "extra": dev.extra or {}
            })
            for dev in active_dest_devices
        ]
        if mirror_payload:
            customer_tables.mirror_rows(mirror_payload)
    except Exception as mirror_err:
        print(f"[Customer Table Mirror Notice After Merge] {mirror_err}")

    return {"moved": moved_devices_count, "into": dest_name}


# Alias for backward compatibility
merge = merge_customers


# ==============================================================================
# SECTION 5: LIFECYCLE MANAGEMENT: SOFT DELETION, RESTORE & PERMANENT PURGE
# ==============================================================================

@router.delete(
    "/{cid}",
    summary="Soft-delete customer and associated devices into recycling bin",
    dependencies=[Depends(require_admin), Depends(require_permission("delete"))]
)
def soft_delete_customer(
    cid: int,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Safely moves a customer organization and all its active devices into the
    recycling bin. Records are not destroyed; they are timestamped with `deleted_at`.
    """
    customer = get_active_customer_or_404(db, cid)
    deletion_timestamp = datetime.utcnow()

    # Step 1: Batch soft-delete all active devices belonging to this customer
    affected_devices_count = (
        db.query(Device)
        .filter(Device.customer_id == customer.id, Device.deleted_at.is_(None))
        .update(
            {
                "deleted_at": deletion_timestamp,
                "deleted_by": admin_user.user_id,
                "delete_reason": f"{CUSTOMER_DELETED_TAG}{customer.name}"
            },
            synchronize_session=False
        )
    )

    # Step 2: Mark customer entity as deleted
    customer.deleted_at = deletion_timestamp
    customer.deleted_by = admin_user.user_id

    log_activity(
        db,
        action="customer_delete",
        detail=f'Moved customer "{customer.name}" to recycling bin ({affected_devices_count} devices tagged).',
        user=admin_user
    )
    db.commit()

    return {"moved_to_bin": customer.id, "devices": affected_devices_count}


# Alias for backward compatibility
delete_customer = soft_delete_customer


@router.post(
    "/{cid}/restore",
    summary="Restore customer and associated devices from recycling bin",
    dependencies=[Depends(require_staff), Depends(require_permission("edit"))]
)
def restore_customer_from_bin(
    cid: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Restores a soft-deleted customer from the recycling bin.
    
    Precision Logic:
    Only restores devices that were deleted TOGETHER with the customer
    (tagged with `Customer deleted: <name>`), preserving records that were
    individually deleted on their own prior to customer deletion.
    """
    customer = db.get(Customer, cid)
    if not customer or customer.deleted_at is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer ID {cid} is not currently in the recycling bin."
        )

    # Step 1: Resurrect only devices deleted with this customer
    restored_devices_count = (
        db.query(Device)
        .filter(
            Device.customer_id == customer.id,
            Device.deleted_at.isnot(None),
            Device.delete_reason.like(f"{CUSTOMER_DELETED_TAG}%")
        )
        .update(
            {
                "deleted_at": None,
                "deleted_by": None,
                "delete_reason": None
            },
            synchronize_session=False
        )
    )

    # Step 2: Clear customer deletion flags
    customer.deleted_at = None
    customer.deleted_by = None

    log_activity(
        db,
        action="customer_restore",
        detail=f'Restored customer "{customer.name}" from recycling bin ({restored_devices_count} devices reactivated).',
        user=current_user
    )
    db.commit()

    return {"restored": customer.id, "devices": restored_devices_count}


# Alias for backward compatibility
restore_customer = restore_customer_from_bin


@router.delete(
    "/{cid}/purge",
    summary="Permanently purge customer and associated devices from database",
    dependencies=[Depends(require_admin), Depends(require_permission("delete"))]
)
def purge_customer_permanently(
    cid: int,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Irrevocably deletes a customer from the recycling bin, permanently purging
    all associated device inventory and dropping the dedicated physical SQL table.
    """
    customer = db.get(Customer, cid)
    if not customer or customer.deleted_at is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer ID {cid} is not in the recycling bin and cannot be purged."
        )

    customer_name = customer.name

    # Step 1: Permanently delete all associated device rows from master table
    deleted_devices_count = (
        db.query(Device)
        .filter(Device.customer_id == customer.id)
        .delete(synchronize_session=False)
    )

    # Step 2: Delete customer record permanently
    db.delete(customer)
    log_activity(
        db,
        action="customer_purge",
        detail=f'Permanently purged customer "{customer_name}" ({deleted_devices_count} devices destroyed).',
        user=admin_user
    )
    db.commit()

    # Step 3: Drop the physical dynamic SQL table in TiDB/SQLite
    try:
        customer_tables.drop_table(cid, customer_name)
    except Exception as table_err:
        print(f"[Physical Table Purge Warning] Could not drop SQL table for {customer_name}: {table_err}")

    return {"purged": cid, "devices": deleted_devices_count}


# Alias for backward compatibility
purge_customer = purge_customer_permanently
