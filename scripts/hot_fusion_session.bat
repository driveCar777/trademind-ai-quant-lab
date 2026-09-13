@echo off
setlocal
REM TradeMind Hot Desk V3 - scheduled session driver (paper only, no real orders, no :9000 calls).
REM Usage: hot_fusion_session.bat open|lunch|close|daily|settle
REM   open  09:35  one Grok named-diagnosis call on ML1 pool + holdings (T-1 bars OK; fills next open)
REM   lunch 11:30  same
REM   close 15:05  same as open (T-1 local bars OK; owner updates :9000 only in the evening)
REM   daily 19:30  settle pending plans; Grok only if today's close plan is missing (never a 4th billable call)
REM   settle       settle only, never Grok
REM Task Scheduler: TradeMind_HotFusionOpen / Lunch / Close / Daily (user-level). :9000 data update stays the owner's button.
set "SESSION=%~1"
if "%SESSION%"=="" set "SESSION=settle"
set "HTTP_PROXY="
set "HTTPS_PROXY="
set "LOG=D:\AGXXAIVER-4-WINDOWS-1-STOCK\data\market\cn_a_share\live\paper_hot\FUSION_DAILY_CRON.log"
echo [%date% %time%] POST /api/v1/hot/fusion/session session=%SESSION% >> "%LOG%"
curl.exe -s -m 30 -X POST "http://127.0.0.1:9001/api/v1/hot/fusion/session" -H "Content-Type: application/json" -d "{\"session\":\"%SESSION%\"}" >> "%LOG%" 2>&1
echo. >> "%LOG%"
endlocal
