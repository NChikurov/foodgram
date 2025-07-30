from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    UserViewSet,
    CustomAuthToken,
    logout_view,
    TagViewSet,
    IngredientViewSet,
    RecipeViewSet
)


router = DefaultRouter()

router.register('users', UserViewSet, basename='user')
router.register('tags', TagViewSet, basename='tag')
router.register('ingredients', IngredientViewSet, basename='ingredient')
router.register('recipes', RecipeViewSet, basename='recipe')

urlpatterns = [
    path('', include(router.urls)),
    path(
        'auth/token/login/',
        CustomAuthToken.as_view(),
        name='api_token_login'
    ),
    path('auth/token/logout/', logout_view, name='api_token_logout'),
]
