@echo off
:: ==============================================================================
:: WHAT IS HAPPENING BELOW:
:: 1. Changes directory into the backend folder relative to this script location.
:: 2. Displays a clean terminal startup banner.
:: 3. Executes `python app.py` which automatically inspects port 8000,
::    falls back to a free port if busy, and runs the Uvicorn ASGI server with live reloading.
:: 4. Pauses if the process exits so any error messages remain readable.
:: ==============================================================================
cd /d "%~dp0backend"
echo ========================================================
echo   Starting BSTPL CustomerVault Backend Server
echo ========================================================
python app.py
pause
