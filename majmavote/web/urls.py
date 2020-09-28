from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from majmavote import settings
from . import views
from .views import Verification, Login

urlpatterns = [
    path('verification', Verification.as_view()),
    path('login', Login.as_view()),
    path('', views.index, name='index'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
