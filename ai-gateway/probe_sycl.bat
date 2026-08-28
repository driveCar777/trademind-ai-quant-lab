@echo off
setlocal
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
call "C:\Program Files (x86)\Intel\oneAPI\setvars.bat" --force
echo === PATH TOOLS ===
where icx
where icpx
where sycl-ls
where ninja
where cmake
echo === SYCL-LS ===
sycl-ls
echo === CMAKE SYCL CONFIG (no build) ===
if not exist D:\s\llama_cpp_python-0.3.34\vendor\llama.cpp (
  echo MISS llama.cpp vendor
  exit /b 2
)
if not exist C:\tmp\sycl-probe mkdir C:\tmp\sycl-probe
cd /d C:\tmp\sycl-probe
cmake -G Ninja -DGGML_SYCL=ON -DCMAKE_C_COMPILER=icx -DCMAKE_CXX_COMPILER=icx -DGGML_SYCL_F16=ON -DGGML_SYCL_TARGET=INTEL D:\s\llama_cpp_python-0.3.34\vendor\llama.cpp
echo CMAKE_EXIT=%ERRORLEVEL%
