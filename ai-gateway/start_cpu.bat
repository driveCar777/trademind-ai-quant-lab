@echo off
setlocal
cd /d D:\AGXXAIVER-4-WINDOWS-1-STOCK\ai-gateway
echo Starting AI Gateway on :9100 (CPU, Qwen2.5-14B-Instruct)
".\.venv\Scripts\python.exe" -m uvicorn server:app --host 0.0.0.0 --port 9100
