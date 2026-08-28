@echo off
setlocal
cd /d D:\AGXXAIVER-4-WINDOWS-1-STOCK
echo ============================================
echo  TradeMind 一键启动 (本机 Master + 通义千问)
echo ============================================
echo.

set "MASTER_BAT=D:\AGXXAIVER-4-WINDOWS-1-STOCK\master\api\start_master.bat"
set "GATEWAY_BAT=D:\AGXXAIVER-4-WINDOWS-1-STOCK\ai-gateway\start_sycl.bat"
set "PY=D:\AGXXAIVER-4-WINDOWS-1-STOCK\master\api\.venv\Scripts\python.exe"
set "STATUS=D:\AGXXAIVER-4-WINDOWS-1-STOCK\scripts\lab_status.py"

"%PY%" "%STATUS%" --check-master
set "MC=%ERRORLEVEL%"
if "%MC%"=="0" (
  echo [9000] 调度中心健康，不重复启动。
) else if "%MC%"=="1" (
  echo [9000] 调度中心未运行，正在新窗口启动...
  start "TradeMind-Master" cmd /k "%MASTER_BAT%"
) else (
  echo [9000] 端口有响应但 /health 不健康，禁止再开第二个窗口。
  exit /b 1
)

"%PY%" "%STATUS%" --check-gateway
set "GC=%ERRORLEVEL%"
if "%GC%"=="0" (
  echo [9100] 通义千问已在跑或正在加载，不重复启动。
) else if "%GC%"=="1" (
  echo [9100] 通义千问未运行，正在新窗口启动 SYCL 网关（加载模型约 1-2 分钟）...
  start "TradeMind-AI-Gateway" cmd /k "%GATEWAY_BAT%"
) else (
  echo [9100] 端口有响应但不是健康网关，禁止再开第二个窗口。
  exit /b 1
)

echo.
echo 等待健康检查...
"%PY%" "D:\AGXXAIVER-4-WINDOWS-1-STOCK\scripts\wait_local.py"
set "RC=%ERRORLEVEL%"

echo.
if "%RC%"=="0" (
  echo 本机启动通过。打开控制台...
  start "" "http://127.0.0.1:9000/dashboard?v=oneclick"
) else (
  echo 本机启动未完全通过。看上面 MASTER_/GATEWAY_ 行。
  echo 通义千问窗口若仍在加载，等 Application startup complete 后再跑:
  echo   %PY% D:\AGXXAIVER-4-WINDOWS-1-STOCK\scripts\wait_local.py
)
exit /b %RC%
