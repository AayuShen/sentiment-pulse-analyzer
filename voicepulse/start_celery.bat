@echo off
echo ============================================
echo  Sentiment Pulse Analyzer - Celery Worker
echo ============================================

REM ---- Purge ALL stale queued tasks ----
echo Purging old queued tasks...
set OMP_NUM_THREADS=1
set MKL_NUM_THREADS=1
set OPENBLAS_NUM_THREADS=1
cd /d "e:\Projects\Sentimental 'Pulse' Analyzer\voicepulse\backend"
"e:\Projects\Sentimental 'Pulse' Analyzer\voicepulse\venv\Scripts\python.exe" -m celery -A tasks purge -f
echo Queue cleared.
echo.

REM ---- Start worker with fresh queue ----
echo Starting worker...
"e:\Projects\Sentimental 'Pulse' Analyzer\voicepulse\venv\Scripts\python.exe" -m celery -A tasks worker --loglevel=info --pool=solo
