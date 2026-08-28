@echo off
setlocal
timeout /t 2 /nobreak >nul
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":9000" ^| findstr LISTENING') do (
  taskkill /PID %%P /F >nul 2>&1
)
timeout /t 1 /nobreak >nul
start "TradeMind-Master" cmd /k "D:\AGXXAIVER-4-WINDOWS-1-STOCK\master\api\start_master.bat"
exit /b 0
