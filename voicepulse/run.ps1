$root = $PSScriptRoot
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"

Write-Host "Starting VoicePulse..." -ForegroundColor Cyan

Write-Host "Starting Redis..." -ForegroundColor Yellow
Start-Process -NoNewWindow -FilePath "redis-server" -ErrorAction SilentlyContinue

Write-Host "Starting Celery worker..." -ForegroundColor Yellow
Start-Process -NoNewWindow -FilePath "celery" -ArgumentList "-A", "tasks", "worker", "--loglevel=info", "--pool=solo" -WorkingDirectory $backend

Write-Host "Starting FastAPI..." -ForegroundColor Yellow
Start-Process -NoNewWindow -FilePath "uvicorn" -ArgumentList "main:app", "--host=0.0.0.0", "--port=8000", "--reload" -WorkingDirectory $backend

Write-Host "Starting Vue dev server..." -ForegroundColor Yellow
Start-Process -NoNewWindow -FilePath "npm" -ArgumentList "run", "dev" -WorkingDirectory $frontend

Write-Host "All services started!" -ForegroundColor Green
Write-Host "  Backend:  http://localhost:8000"
Write-Host "  Frontend: http://localhost:5173"
Write-Host "  API docs: http://localhost:8000/docs"
