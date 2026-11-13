@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
rem يغير كلمة سر المستخدم postgres بالداتابيس المحلية ويفعّل pgvector
rem الخطوات: نسخة احتياطية من pg_hba.conf - دخول بدون كلمة سر من هذا الجهاز بس - تغيير كلمة السر - إرجاع الملف الأصلي
set "PGBIN=%~dp0postgres_local\venv\Lib\site-packages\pgserver\pginstall\bin"
set "PGDATA=%~dp0postgres_local\data"

"%PGBIN%\pg_ctl.exe" -D "%PGDATA%" status >nul 2>nul || "%PGBIN%\pg_ctl.exe" -D "%PGDATA%" -l postgres_local\server.log -o "-p 5432 -h localhost" -w start

copy /y "%PGDATA%\pg_hba.conf" "%PGDATA%\pg_hba.conf.bak" >nul || (echo [خطأ] ما گدرنا ناخذ نسخة احتياطية & pause & exit /b 1)
(echo host    all             postgres        127.0.0.1/32            trust& type "%PGDATA%\pg_hba.conf.bak") > "%PGDATA%\pg_hba.conf"
"%PGBIN%\pg_ctl.exe" -D "%PGDATA%" reload >nul

echo.
echo اكتبي كلمة السر الجديدة للمستخدم postgres مرتين (ما تبين وانتي تكتبين):
"%PGBIN%\psql.exe" -h 127.0.0.1 -U postgres -d bot_db -c "\password postgres"
set "PWERR=%errorlevel%"
"%PGBIN%\psql.exe" -h 127.0.0.1 -U postgres -d bot_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
set "EXTERR=%errorlevel%"

rem إرجاع الملف الأصلي (رجعت كلمة السر مطلوبة)
copy /y "%PGDATA%\pg_hba.conf.bak" "%PGDATA%\pg_hba.conf" >nul
"%PGBIN%\pg_ctl.exe" -D "%PGDATA%" reload >nul
del "%PGDATA%\pg_hba.conf.bak"

if not "%PWERR%"=="0" echo [خطأ] كلمة السر ما تغيرت
if not "%EXTERR%"=="0" (echo [خطأ] ما انفعلت إضافة pgvector & pause & exit /b 1)

venv\Scripts\python.exe -X utf8 manage.py migrate university || (pause & exit /b 1)
echo.
echo تمام: كلمة السر تغيرت، pgvector مفعّل، والمايغريشن انطبق. احفظي كلمة السر بمكان آمن.
pause
