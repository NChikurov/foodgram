from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

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
    - GET /api/users/ - список пользователей;
    - POST /api/users/ - регистрация;
    - GET /api/users/{id}/ - профиль пользователя;
    - PUT/PATCH /api/users/{id}/ - обновление пользователя;
    - DELETE /api/users/{id}/ - удаление профиля.
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
        - GET /api/users/me/ - мой профиль;
        - PUT/PATCH /api/users/me - обновить профиль.
        """
        user = request.user

        if request.method == 'GET':
            serializer = UserSerializer(user, context={'request': request})
            return Response(serializer.data)
        
        serializer = UserUpdateSerializer(
            user,
            data=request.data,
            partial=(request.method == 'PATCH')
        )

        if serializer.is_valid():
            serializer.save()
            response_serializer = UserSerializer(user, context={'request': request})
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
        - PUT /api/users/me/avatar/ - загрузить аватар;
        - DELETE /api/users/me/avatar/ - удалить аватар.
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
            user.avatar.delete(save=False)
            user.avatar = None
            user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        url_path='set_password'
    )
    def set_password(self, request):
        """
        Смена пароля для текущего пользователя: 
        - POST /api/users/set_password/
        """
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')

        if not current_password:
            return Response(
                {'current_password': ['Обязательное поле']},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not new_password:
            return Response(
                {'new_password': ['Обязательное поле']},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not user.check_password(current_password):
            return Response(
                {'current_password': ['Неверный пароль']},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return Response(
                {'new_password': e.messages},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(new_password)
        user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)
