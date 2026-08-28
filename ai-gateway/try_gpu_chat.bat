@echo off
setlocal
cd /d D:\AGXXAIVER-4-WINDOWS-1-STOCK\ai-gateway
set "VS2022INSTALLDIR=C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools"
call "%VS2022INSTALLDIR%\VC\Auxiliary\Build\vcvars64.bat"
call "C:\Program Files (x86)\Intel\oneAPI\setvars.bat" --force
echo Using default SYCL device after setvars
".\.venv\Scripts\python.exe" try_gpu_chat.py
echo EXIT=%ERRORLEVEL%
