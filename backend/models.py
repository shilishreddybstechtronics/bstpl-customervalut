"""models.py - the table / column layout of CustomerVault.

One MySQL table per customer (the table name is the customer name) plus the system tables
(customers, employees, sessions, column_registry, app_state, activity_log, trash_bin).
The definitions live in database.py; they are listed here for reference:
    from models import STANDARD, SYSTEM
"""
from database import (
    STANDARD,
    OPTIONAL_KNOWN,
    ALWAYS_COLUMNS,
    REQUIRED_DB,
    RESERVED_DB,
    RESERVED_LABELS,
    SYSTEM,
    TABLE_OPTS,
    GID,
)
