@echo off
setlocal
REM TradeMind Hot Desk V3 - daily driver (paper only, no real orders).
REM Calls POST /api/v1/hot/fusion/daily on :9001:
REM   (a) settle pending fusion plans at their fill_date OPEN (simulated fills into live/paper_hot/JOURNAL.json)
REM   (b) if bars are fresh for the last completed session, run the fusion pipeline (2 Grok calls) for that asof;
REM       stale bars -> SKIPPED_STALE_DATA, Grok is NOT called.
REM
REM :9000's data update is the owner's button. This script never triggers :9000. Run it AFTER the owner has
REM updated :9000 data (Task Scheduler: TradeMind_HotFusionDaily, 19:30 Mon-Fri). If :9001 is down, nothing happens.
set "HTTP_PROXY="
set "HTTPS_PROXY="
set "LOG=D:\AGXXAIVER-4-WINDOWS-1-STOCK\data\market\cn_a_share\live\paper_hot\FUSION_DAILY_CRON.log"
echo [%date% %time%] POST /api/v1/hot/fusion/daily >> "%LOG%"
curl.exe -s -m 30 -X POST "http://127.0.0.1:9001/api/v1/hot/fusion/daily" -H "Content-Type: application/json" -d "{}" >> "%LOG%" 2>&1
echo. >> "%LOG%"
endlocal
