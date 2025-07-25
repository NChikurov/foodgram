from django.urls import path, include

from rest_framework.routers import DefaultRouter
from rest_framework.authtoken import views as auth_views

from .views import UserViewSet


router = DefaultRouter()

router.register('users', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/token/login/', auth_views.obtain_auth_token, name='api_token_login'),
]
