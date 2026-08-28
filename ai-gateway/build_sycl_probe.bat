@echo off
setlocal
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
call "C:\Program Files (x86)\Intel\oneAPI\setvars.bat" --force
if not exist C:\tmp\sycl-probe-rel mkdir C:\tmp\sycl-probe-rel
cd /d C:\tmp\sycl-probe-rel
cmake -G Ninja -DCMAKE_BUILD_TYPE=Release -DGGML_SYCL=ON -DCMAKE_C_COMPILER=icx -DCMAKE_CXX_COMPILER=icx -DGGML_SYCL_F16=ON -DGGML_SYCL_TARGET=INTEL -DGGML_BUILD_TESTS=OFF -DGGML_BUILD_EXAMPLES=OFF -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=OFF -DLLAMA_BUILD_SERVER=OFF D:\s\llama_cpp_python-0.3.34\vendor\llama.cpp
if errorlevel 1 exit /b 1
cmake --build . --target ggml-sycl --parallel
echo BUILD_EXIT=%ERRORLEVEL%
