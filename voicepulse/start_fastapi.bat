@echo off
set OMP_NUM_THREADS=1
set MKL_NUM_THREADS=1
set OPENBLAS_NUM_THREADS=1
cd /d "e:\Projects\Sentimental 'Pulse' Analyzer\voicepulse\backend"
"e:\Projects\Sentimental 'Pulse' Analyzer\voicepulse\venv\Scripts\python.exe" -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
