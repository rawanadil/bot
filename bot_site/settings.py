from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "dev-only-change-me"
DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

INSTALLED_APPS = [
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
]

ROOT_URLCONF = "bot_site.urls"
WSGI_APPLICATION = "bot_site.wsgi.application"

# نفس مجلدات نسخة Flask: template و static
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "template"],
        "APP_DIRS": False,
    },
]
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

DATABASES = {}
USE_TZ = True
