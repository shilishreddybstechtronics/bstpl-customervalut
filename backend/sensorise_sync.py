"""
Sensorise Telematics Synchronization Module (backend/sensorise_sync.py)
Re-exports synchronization helpers directly from the backend/sensorise package.
"""

import sys
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

try:
    from sensorise.sensorise_sync import (
        sync_devices_with_sensorise,
        sync_device_dicts_with_sensorise,
        fetch_sensorise_telematics_for_iccids,
        _clean_iccid_term,
        _extract_numeric_iccid,
        _parse_sensorise_date
    )
except ImportError:
    from backend.sensorise.sensorise_sync import (
        sync_devices_with_sensorise,
        sync_device_dicts_with_sensorise,
        fetch_sensorise_telematics_for_iccids,
        _clean_iccid_term,
        _extract_numeric_iccid,
        _parse_sensorise_date
    )

__all__ = [
    "sync_devices_with_sensorise",
    "sync_device_dicts_with_sensorise",
    "fetch_sensorise_telematics_for_iccids",
    "_clean_iccid_term",
    "_extract_numeric_iccid",
    "_parse_sensorise_date"
]
