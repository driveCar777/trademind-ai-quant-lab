@echo off
setlocal
set "VS2022INSTALLDIR=C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools"
call "%VS2022INSTALLDIR%\VC\Auxiliary\Build\vcvars64.bat"
call "C:\Program Files (x86)\Intel\oneAPI\setvars.bat" --force
if not exist C:\tmp\icx mkdir C:\tmp\icx
set TMP=C:\tmp\icx
set TEMP=C:\tmp\icx
set TMPDIR=C:\tmp\icx
set CMAKE_GENERATOR=Ninja
set CMAKE_ARGS=-DGGML_SYCL=ON -DCMAKE_C_COMPILER=icx -DCMAKE_CXX_COMPILER=icx -DGGML_SYCL_F16=OFF -DGGML_SYCL_TARGET=INTEL
cd /d D:\s\llama_cpp_python-0.3.34
"D:\AGXXAIVER-4-WINDOWS-1-STOCK\ai-gateway\.venv\Scripts\python.exe" -m pip install . --no-build-isolation --force-reinstall --no-deps
echo PIP_EXIT=%ERRORLEVEL%
