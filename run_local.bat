@echo off
rem Start the local PostgreSQL + Django site with one command.
rem Keep this file ASCII only: cmd misreads Arabic text in .bat files.
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PGBIN=%~dp0postgres_local\venv\Lib\site-packages\pgserver\pginstall\bin"

rem Start PostgreSQL if it is not running
"%PGBIN%\pg_ctl.exe" -D "%~dp0postgres_local\data" status >nul 2>nul
if errorlevel 1 (
  echo Starting database...
  "%PGBIN%\pg_ctl.exe" -D "%~dp0postgres_local\data" -l "%~dp0postgres_local\server.log" -o "-p 5432 -h localhost" -w start
  if errorlevel 1 (
    echo [ERROR] Database did not start. See postgres_local\server.log
    pause
    exit /b 1
  )
)

echo.
echo Site: http://127.0.0.1:8000   (press Ctrl+C to stop)
start "" http://127.0.0.1:8000
"%~dp0venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8000
