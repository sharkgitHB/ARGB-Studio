@echo off
rem ARGB Studio - standalone launcher (auto-elevates for motherboard access)
rem Prefers the bundled Python; falls back to a local venv, then system Python.
cd /d "%~dp0"

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrator rights...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

if exist "runtime\python\pythonw.exe" (
    start "" "runtime\python\pythonw.exe" main.py
    exit /b
)

if not exist ".venv\Scripts\python.exe" (
    echo First run: setting up environment, please wait...
    python -m venv .venv
    ".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
)
start "" ".venv\Scripts\pythonw.exe" main.py
