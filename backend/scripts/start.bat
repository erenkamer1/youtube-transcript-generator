@echo off
cd /d %~dp0..
call .venv\Scripts\activate.bat
python scripts\kill_port.py 8000
netstat -ano | findstr "127.0.0.1:8000" | findstr LISTENING >nul
if %errorlevel%==0 (
  echo.
  echo UYARI: Port 8000 hala dolu. Gorev Yoneticisi'nden tum python.exe sureclerini sonlandirin
  echo veya: taskkill /IM python.exe /F
  echo.
  pause
  exit /b 1
)
echo Backend baslatiliyor...
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
