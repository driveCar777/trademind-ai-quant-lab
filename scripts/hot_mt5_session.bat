@echo off
setlocal
REM TradeMind Hot Desk — AVA MT5 product session (demo only; never :9000).
REM Usage: hot_mt5_session.bat asia|ny|settle
REM   asia   08:30  one Grok call across gold/oil/FX books; live ticks from the terminal
REM   ny     20:30  same
REM   settle        no Grok
set "SESSION=%~1"
if "%SESSION%"=="" set "SESSION=settle"
set "HTTP_PROXY="
set "HTTPS_PROXY="
set "LOG=D:\AGXXAIVER-4-WINDOWS-1-STOCK\data\market\cn_a_share\live\paper_hot\MT5_CRON.log"
echo [%date% %time%] POST /api/v1/hot/mt5/session session=%SESSION% >> "%LOG%"
curl.exe -s -m 30 -X POST "http://127.0.0.1:9001/api/v1/hot/mt5/session" -H "Content-Type: application/json" -d "{\"session\":\"%SESSION%\"}" >> "%LOG%" 2>&1
echo. >> "%LOG%"
endlocal
