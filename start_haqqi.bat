@echo off
cd /d C:\Users\Laptop\Desktop\haqqi
echo Starting Haqqi server...
python -m uvicorn app.main:app --port 8000 --host 0.0.0.0
pause
