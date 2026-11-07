@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Creating the Python environment. This runs only once...
  python -m venv .venv
  .venv\Scripts\python.exe -m pip install -r requirements.txt
)

for /f %%i in ('powershell -NoProfile -Command "(Get-NetIPAddress -AddressFamily IPv4 ^| Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' } ^| Select-Object -First 1).IPAddress"') do set LANIP=%%i

set HOST=0.0.0.0
set PORT=5000

echo.
echo   RoadWatch is starting.
echo   This computer:  http://127.0.0.1:5000
if defined LANIP echo   Other devices: http://%LANIP%:5000
echo                  http://%COMPUTERNAME%.local:5000
echo.
echo   Keep this window open while using the site. Press Ctrl+C to stop.
echo.

start "" /b powershell -NoProfile -Command "Start-Sleep -Seconds 3; Start-Process 'http://127.0.0.1:5000'"
.venv\Scripts\python.exe app.py

endlocal
