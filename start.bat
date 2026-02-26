@echo off
echo Starting Financial Document Analyzer...

echo Starting Redis (make sure Redis is installed)...
start "Redis" cmd /k "redis-server"

timeout /t 2

echo Starting Celery Worker...
start "Celery" cmd /k "celery -A celery_worker worker --loglevel=info --concurrency=4"

timeout /t 2

echo Starting FastAPI Server...
start "FastAPI" cmd /k "python main.py"

echo All services started!
echo API available at: http://localhost:8000
echo API Docs at: http://localhost:8000/docs
