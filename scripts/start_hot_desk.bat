@echo off
setlocal
cd /d D:\AGXXAIVER-4-WINDOWS-1-STOCK\master\api
set "TRADEMIND_CURSOR_API_KEY_FILE=D:\Cursor\APIKey.txt"
set "TRADEMIND_HOT_SMOKE="
set "HTTP_PROXY="
set "HTTPS_PROXY="
echo Starting TradeMind Hot Desk on :9001
echo Frozen V2.1 paper stays at http://127.0.0.1:9000/paper
echo This desk: http://127.0.0.1:9001/paper
".\.venv\Scripts\python.exe" -m uvicorn app.hot_main:app --host 0.0.0.0 --port 9001
