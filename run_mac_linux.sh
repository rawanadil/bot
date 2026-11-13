#!/usr/bin/env bash
# تشغيل مشروع بوابة كلية الهندسة على ماك أو لينكس
set -e
cd "$(dirname "$0")"

command -v python3 >/dev/null || { echo "Python مو منصب"; exit 1; }
command -v psql >/dev/null || { echo "PostgreSQL مو منصب (ماك: brew install postgresql@16 && brew services start postgresql@16)"; exit 1; }

# إنشاء الداتابيس (مرة وحدة). على ماك المستخدم الافتراضي هو اسم حسابك، وعلى لينكس postgres
if [ "$(uname)" = "Darwin" ]; then PSQL="psql -d postgres"; else PSQL="sudo -u postgres psql"; fi
$PSQL -tAc "SELECT 1 FROM pg_roles WHERE rolname='bot_user'" | grep -q 1 || $PSQL -c "CREATE USER bot_user WITH PASSWORD 'bot_pass' CREATEDB;"
$PSQL -tAc "SELECT 1 FROM pg_database WHERE datname='bot_db'" | grep -q 1 || $PSQL -c "CREATE DATABASE bot_db OWNER bot_user;"
# تفعيل pgvector (ماك: brew install pgvector، لينكس: apt install postgresql-16-pgvector)
if [ "$(uname)" = "Darwin" ]; then psql -d bot_db -c "CREATE EXTENSION IF NOT EXISTS vector;"; else sudo -u postgres psql -d bot_db -c "CREATE EXTENSION IF NOT EXISTS vector;"; fi

[ -d venv ] || python3 -m venv venv
. venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
python manage.py migrate
python manage.py create_demo_data

echo
echo "الموقع شغال على http://127.0.0.1:8000"
echo "الحسابات: student1@uni.edu / student4@uni.edu / teacher@uni.edu / admin@uni.edu"
echo "كلمة السر: demo12345"
python manage.py runserver
