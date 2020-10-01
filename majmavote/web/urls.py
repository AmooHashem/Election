from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.urls import path, include, re_path

from majmavote import settings
from . import views
from .views import Verification, Login, ElectionView, VoteView, ResultView, RegisterView

urlpatterns = [
    path('verification', Verification.as_view()),
    path('login', Login.as_view()),
    path('logout', views.logout_view, name='logout_view'),
    path('election', login_required(ElectionView.as_view())),
    path('register', staff_member_required(RegisterView.as_view())),
    re_path(r'^election/(\d)', login_required((VoteView.as_view()))),
    re_path(r'^election/result/(\d)', staff_member_required((ResultView.as_view()))),
    path('', views.index, name='index'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
