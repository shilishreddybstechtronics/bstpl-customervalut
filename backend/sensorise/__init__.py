"""
Sensorise Integration Package (backend/sensorise/)
black shield technologies pvt ltd (BSTPL) — CustomerVault
Provides service modules, API connectors, and ingestion utilities for Sensorise IoT/M2M eSIM data.
"""

import sys
import os

_pkg_dir = os.path.dirname(os.path.abspath(__file__))
if _pkg_dir not in sys.path:
    sys.path.insert(0, _pkg_dir)

from .config import (
    DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME,
    SENSORISE_SERVER_URL, SENSORISE_RELATION_ID, SENSORISE_SHARED_KEY,
    SENSORISE_AUTH_TOKEN, SENSORISE_TOKEN_EXPIRY
)
from .sensorise import SensoriseClient, sensorise_client, get_client
from .sensorise_sync import sync_devices_with_sensorise, sync_device_dicts_with_sensorise, fetch_sensorise_telematics_for_iccids
from . import db
from . import app_logger

__all__ = [
    "SensoriseClient",
    "sensorise_client",
    "get_client",
    "sync_devices_with_sensorise",
    "sync_device_dicts_with_sensorise",
    "fetch_sensorise_telematics_for_iccids",
    "db",
    "app_logger",
    "DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD", "DB_NAME",
    "SENSORISE_SERVER_URL", "SENSORISE_RELATION_ID", "SENSORISE_SHARED_KEY",
    "SENSORISE_AUTH_TOKEN", "SENSORISE_TOKEN_EXPIRY"
]
