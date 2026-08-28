@echo off
setlocal
cd /d D:\AGXXAIVER-4-WINDOWS-1-STOCK\ai-gateway
set "VS2022INSTALLDIR=C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools"
call "%VS2022INSTALLDIR%\VC\Auxiliary\Build\vcvars64.bat"
call "C:\Program Files (x86)\Intel\oneAPI\setvars.bat" --force
set GGML_SYCL_F16=OFF
rem Do not set ONEAPI_DEVICE_SELECTOR — it breaks llama_backend_init.
echo Starting AI Gateway on :9100 with SYCL (Qwen2.5-14B-Instruct, F16=OFF)
".\.venv\Scripts\python.exe" -m uvicorn server:app --host 0.0.0.0 --port 9100
