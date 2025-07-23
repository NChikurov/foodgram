from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Разрешает редактирование только владельцу объекта.
    Остальным - только чтение.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj == request.user


class IsOwner(permissions.BasePermission):
    """
    Разрешает доступ только владельцу объекта.
    """
    def has_object_permission(self, request, view, obj):
        return obj == request.user


class IsAuthenticatedOrCreateReadOnly(permissions.BasePermission):
    """
    Разрешает:
    - регистрацию всем пользователям (POST);
    - чтение всем пользователям (GET);
    - остальные действия только авторизованным пользователям.
    """
    def has_permission(self, request, view):
        if reqest.method in ['GET', 'POST']:
            return True

        return request.user and request.user.is_authenticated
