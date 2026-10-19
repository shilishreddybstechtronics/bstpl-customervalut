"""schemas.py - the error types the API reports back to the website (duplicate IMEI, customer already exists).

The request bodies are plain JSON validated in database.py / main.py.
"""
from database import (
    DuplicateIMEI,
    CustomerExists,
)
