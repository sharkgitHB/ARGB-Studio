@echo off
rem Used by the "ARGB Studio" scheduled task (already elevated at logon)
cd /d "%~dp0"
if exist "runtime\python\pythonw.exe" (
    start "" "runtime\python\pythonw.exe" main.py
    exit /b
)
if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" main.py
) else (
    start "" pythonw main.py
)
