@echo off
setlocal
cd /d D:\AGXXAIVER-4-WINDOWS-1-STOCK
title TradeMind 一键启动
echo ============================================
echo  TradeMind 实验室一键启动
echo  本机调度中心 + 通义千问 + Xavier 四台
echo ============================================
echo.
echo 已经健康的服务会跳过。结束时按项列出状态。
echo.

set "PY=D:\AGXXAIVER-4-WINDOWS-1-STOCK\master\api\.venv\Scripts\python.exe"
set "STATUS=D:\AGXXAIVER-4-WINDOWS-1-STOCK\scripts\lab_status.py"

call "D:\AGXXAIVER-4-WINDOWS-1-STOCK\start_all.bat"
set "LOCAL_RC=%ERRORLEVEL%"

echo.
echo ---- Xavier-01/02/03/04 ----
call "D:\AGXXAIVER-4-WINDOWS-1-STOCK\start_xavier.bat"
set "X_RC=%ERRORLEVEL%"

echo.
echo ---- 当前状态 ----
"%PY%" "%STATUS%"
set "ST=%ERRORLEVEL%"

echo.
echo ============================================
echo 控制台：http://127.0.0.1:9000/dashboard
if "%ST%"=="0" (
  echo 结果：六项都在线。已经健康的没有重复启动。
  powershell -NoProfile -Command "Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show('六项都在线（调度中心、通义千问、四台 Xavier）。已经健康的没有重复启动。','TradeMind 一键启动')"
  pause
  exit /b 0
)
if "%ST%"=="1" (
  echo 结果：调度中心不健康。本机=%LOCAL_RC%  Xavier=%X_RC%
  powershell -NoProfile -Command "Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show('调度中心不健康。请看黑色窗口 LAB_STATUS。','TradeMind 一键启动')"
  pause
  exit /b 1
)
echo 结果：有项目离线或通义千问仍在加载。本机=%LOCAL_RC%  Xavier=%X_RC%
echo 请看上面的 LAB_STATUS，不要当成全部就绪。
powershell -NoProfile -Command "Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show('未全部在线。请看黑色窗口 LAB_STATUS 哪一项是 OFFLINE / LOADING。','TradeMind 一键启动')"
pause
exit /b 1
