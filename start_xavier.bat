@echo off
setlocal
echo 拉起 Xavier-01/02/03/04（已在线则跳过）
"D:\AGXXAIVER-4-WINDOWS-1-STOCK\master\api\.venv\Scripts\python.exe" "D:\AGXXAIVER-4-WINDOWS-1-STOCK\scripts\start_xavier_workers.py"
exit /b %ERRORLEVEL%
