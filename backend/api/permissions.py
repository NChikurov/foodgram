from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Разрешает редактирование только владельцу объекта.
    Остальным - только чтение.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if hasattr(obj, 'author'):
            return obj.author == request.user
        
        return obj == request.user


class IsOwner(permissions.BasePermission):
    """
    Разрешает доступ только владельцу объекта.
    """
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'author'):
            return obj.author == request.user
        return obj == request.user


class IsRecipeAuthorOrReadOnly(permissions.BasePermission):
    """
    Специальные права для рецептов:
    - Читать могут все
    - Изменять только автор рецепта
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user


class IsAuthenticatedOrCreateReadOnly(permissions.BasePermission):
    """
    Разрешает:
    - регистрацию всем пользователям (POST);
    - чтение всем пользователям (GET);
    - остальные действия только авторизованным пользователям.
    """
    def has_permission(self, request, view):
        if request.method in ['GET', 'POST']:
            return True
        elif request.method == 'POST' and view.action == 'create':
            return True

        return request.user and request.user.is_authenticated
