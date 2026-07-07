@echo off
cd /d %~dp0
set UV=C:\Users\user4\AppData\Local\Python\pythoncore-3.14-64\Scripts\uv.exe
echo [1/2] Applying DB migration...
"%UV%" run alembic upgrade head
echo.
echo [2/2] Starting app: http://localhost:8000
"%UV%" run uvicorn work_dashboard.main:app --reload --host 127.0.0.1 --port 8000
