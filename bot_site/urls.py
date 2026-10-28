from django.urls import path

from . import views

urlpatterns = [
    path("chat", views.chat_page),
    path("ask_chat", views.ask_chat),
    path("ee.html", views.ee_page),
    path("pas", views.home),
    path("ask_pas", views.ask_pas),
]
