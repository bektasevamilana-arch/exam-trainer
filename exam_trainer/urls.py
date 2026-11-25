from django.urls import path

from trainer import views

urlpatterns = [
    path("", views.home, name="home"),
    path("topics/<slug:slug>/", views.quiz, name="quiz"),
]
