from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from . import views

urlpatterns = [
    path("admin/", admin.site.urls),  # لوحة التحكم
    path("chat", views.chat_page),
    path("ask_chat", views.ask_chat),
    path("ee.html", views.ee_page),
    path("pas", views.home),
    path("ask_pas", views.ask_pas),
]

# عرض الملفات المرفوعة أثناء التطوير
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
