@echo off
setlocal
cd /d D:\AGXXAIVER-4-WINDOWS-1-STOCK\master\api
echo Starting TradeMind Master API on :9000
echo Dashboard: http://127.0.0.1:9000/dashboard
".\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 9000
