import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "dev-only-change-me"
DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

INSTALLED_APPS = [
    "django.contrib.admin",          # لوحة التحكم /admin
    "django.contrib.auth",           # تسجيل الدخول والصلاحيات
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.postgres",       # حقول خاصة بـ PostgreSQL (بصمة الوجه)
    "django.contrib.staticfiles",
    "university",                    # تطبيق الجامعة (الداتابيس)
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "bot_site.urls"
WSGI_APPLICATION = "bot_site.wsgi.application"

# نفس مجلدات نسخة Flask: template و static
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "template"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

# ================== قاعدة البيانات PostgreSQL ==================
# القيم تنقرا من متغيرات البيئة، وإذا ماكو تستخدم القيم الافتراضية
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "bot_db"),
        "USER": os.environ.get("DB_USER", "bot_user"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "bot_pass"),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    }
}

# جدول المستخدمين الخاص بينا (الدخول بالإيميل الجامعي)
AUTH_USER_MODEL = "university.User"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# الملفات المرفوعة (صور، PDF، Excel) تنحفظ هنا، والداتابيس تخزن المسار بس
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

LANGUAGE_CODE = "ar"
TIME_ZONE = "Asia/Baghdad"
USE_I18N = True
USE_TZ = True
