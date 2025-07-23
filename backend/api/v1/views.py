from django.contrib.auth import get_user_model

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .serializers import(
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer
)
from .permissions import IsOwnerOrReadOnly, IsAuthenticatedOrCreateReadOnly


User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """
    Вьюсет для работы с пользователями.

    Автоматически создает эндпоинты:
    - GET /api/v1/users/ - список пользователей;
    - POST /api/v1/users/ - регистрация;
    - GET /api/v1/users/{id}/ - профиль пользователя;
    - PUT/PATCH /api/v1/users/{id}/ - обновление пользователя;
    - DELETE /api/v1/users/{id}/ - удаление профиля.
    """
    queryset = User.objects.all()
    permission_classes = [IsAuthenticatedOrCreateReadOnly, IsOwnerOrReadOnly]

    def get_serializer_class(self):
        """Выбираем сериализатор в зависимости от действия."""
        if self.action == 'create':
            return UserCreateSerializer
        
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
                
        return UserSerializer
    
    @action(
        detail=False,
        methods=['get', 'put', 'patch'],
        permission_classes=[IsAuthenticated],
        url_path='me'
    )
    def me(self, request):
        """
        Работа с текущим пользователем:
        - GET /api/v1/users/me/ - мой профиль;
        - PUT/PATCH /api/v1/users/me - обновить профиль.
        """
        user = request.user

        if request.method == 'GET':
            serializer = UserSerializer(user)
            return Response(serializer.data)
        
        serializer = UserUpdateSerializer(
            user,
            data=request.data,
            partial=(request.method == 'PATCH')
        )

        if serializer.is_valid():
            serializer.save()
            response_serializer = UserSerializer(user)
            return Response(response_serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='me/avatar'
    )
    def avatar(self, request):
        """
        Работа с аватаром:
        - PUT /api/v1/users/me/avatar/ - загрузить аватар;
        - DELETE /api/v1/users/me/avatar/ - удалить аватар.
        """
        user = request.user

        if request.method == 'PUT':
            if 'avatar' not in request.data:
                return Response(
                    {'avatar': ['Это поле обязательно.']},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user.avatar = request.data['avatar']
            user.save()

            return Response({
                'avatar': user.avatar.url if user.avatar else None
            })


        if user.avatar:
            user.avatar.delete()
            user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)