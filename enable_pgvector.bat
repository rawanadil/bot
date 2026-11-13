@echo off
chcp 65001 >nul
cd /d "%~dp0"
rem يفعل إضافة pgvector بالداتابيس المحلية (مرة وحدة) ويطبق المايغريشن
set "PGBIN=%~dp0postgres_local\venv\Lib\site-packages\pgserver\pginstall\bin"
"%PGBIN%\pg_ctl.exe" -D postgres_local\data status >nul 2>nul || "%PGBIN%\pg_ctl.exe" -D postgres_local\data -l postgres_local\server.log -o "-p 5432 -h localhost" -w start

echo اكتبي كلمة سر المستخدم postgres (superuser) لما ينطلب منج:
"%PGBIN%\psql.exe" -U postgres -h localhost -d bot_db -c "CREATE EXTENSION IF NOT EXISTS vector;" || (echo [خطأ] ما انفعلت الإضافة & pause & exit /b 1)

venv\Scripts\python.exe -X utf8 manage.py migrate university || (pause & exit /b 1)
echo تمام: pgvector مفعّل. لحساب متجهات أسئلة الشات بوت: venv\Scripts\python.exe manage.py embed_faqs
pause
