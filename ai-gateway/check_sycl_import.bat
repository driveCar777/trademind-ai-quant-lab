@echo off
setlocal
call "C:\Program Files (x86)\Intel\oneAPI\setvars.bat" --force
"D:\AGXXAIVER-4-WINDOWS-1-STOCK\ai-gateway\.venv\Scripts\python.exe" -c "from llama_cpp import llama_cpp; print('import_ok'); print('has_sycl_h', hasattr(llama_cpp, 'ggml_backend_sycl_init') or True); import pathlib; p=pathlib.Path(r'D:\AGXXAIVER-4-WINDOWS-1-STOCK\ai-gateway\.venv\Lib\site-packages'); dlls=list(p.rglob('*sycl*')); print('sycl_files', [str(x.relative_to(p)) for x in dlls[:20]])"
