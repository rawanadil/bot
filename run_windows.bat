@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
echo ==========================================
echo   تشغيل مشروع بوابة كلية الهندسة
echo ==========================================

rem ---- 1) التأكد من Python ----
where python >nul 2>nul
if errorlevel 1 (
  echo [خطأ] Python مو منصب. نصبيه من python.org وفعلي خيار "Add Python to PATH"
  pause & exit /b 1
)

rem ---- 2) البحث عن PostgreSQL ----
set "PSQL="
where psql >nul 2>nul && set "PSQL=psql"
if not defined PSQL for /d %%D in ("C:\Program Files\PostgreSQL\*") do if exist "%%D\bin\psql.exe" set "PSQL=%%D\bin\psql.exe"
if not defined PSQL (
  echo [خطأ] PostgreSQL مو منصب. نصبيه من postgresql.org واحفظي كلمة سر المستخدم postgres
  pause & exit /b 1
)

rem ---- 3) إنشاء الداتابيس (مرة وحدة) ----
set /p PGPASSWORD=اكتبي كلمة سر المستخدم postgres (اللي حطيتيها وقت تنصيب PostgreSQL): 
"%PSQL%" -U postgres -h localhost -tAc "SELECT 1 FROM pg_roles WHERE rolname='bot_user'" | find "1" >nul || "%PSQL%" -U postgres -h localhost -c "CREATE USER bot_user WITH PASSWORD 'bot_pass' CREATEDB;"
"%PSQL%" -U postgres -h localhost -tAc "SELECT 1 FROM pg_database WHERE datname='bot_db'" | find "1" >nul || "%PSQL%" -U postgres -h localhost -c "CREATE DATABASE bot_db OWNER bot_user;"
rem تفعيل pgvector (لازم superuser). إذا فشل: نصبي pgvector من github.com/pgvector/pgvector
"%PSQL%" -U postgres -h localhost -d bot_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
if errorlevel 1 (
  echo [خطأ] ما گدرنا نسوي الداتابيس. تأكدي من كلمة السر وإن PostgreSQL شغال
  pause & exit /b 1
)
set "PGPASSWORD="

rem ---- 4) تنصيب المكتبات ----
if not exist venv python -m venv venv
call venv\Scripts\activate.bat
python -m pip install -q --upgrade pip
pip install -q -r requirements.txt || (echo [خطأ] فشل تنصيب المكتبات & pause & exit /b 1)

rem ---- 5) الجداول والبيانات التجريبية ----
python manage.py migrate || (echo [خطأ] فشل إنشاء الجداول & pause & exit /b 1)
python manage.py create_demo_data

rem ---- 6) التشغيل ----
echo.
echo الموقع شغال على http://127.0.0.1:8000
echo الحسابات: student1@uni.edu / student4@uni.edu / teacher@uni.edu / admin@uni.edu
echo كلمة السر: demo12345
echo للإيقاف اضغطي Ctrl+C
start "" http://127.0.0.1:8000
python manage.py runserver
pause
