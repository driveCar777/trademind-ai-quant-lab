@echo off
REM TradeMind A-share desktop GUI launcher (Windows).
REM First run: creates a local venv and installs PySide6.
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo [setup] creating venv and installing PySide6 ...
  py -3 -m venv .venv || python -m venv .venv
  ".venv\Scripts\python.exe" -m pip install --upgrade pip
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
)

echo [run] starting TradeMind A-share desktop ...
".venv\Scripts\python.exe" -m ashare_desktop
