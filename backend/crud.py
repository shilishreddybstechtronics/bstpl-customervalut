"""crud.py - the data operations of CustomerVault (create / read / update / delete records, customers, trash, users).

The code itself lives in database.py (it shares one MySQL pool and locks, so it is kept in one place).
This module is the single list of those operations: import what you need from here, e.g.
    from crud import create_device, list_devices
"""
from database import (
    create_device,
    list_devices,
    bulk_fetch,
    update_device,
    delete_device,
    create_member,
    import_groups,
    sheet_upload,
    apply_sim_data,
    rename_customer,
    rename_customers,
    merge_customers,
    delete_customer,
    list_trash,
    trash_view,
    restore_trash,
    purge_trash,
    alerts,
    bootstrap,
    register,
    login,
    change_password,
    check_user,
)
