from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.http import HttpResponse

from rest_framework import viewsets, status
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from .serializers import (
    UserSerializer,
    UserWithRecipesSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    TagSerializer,
    IngredientSerializer,
    RecipeSerializer,
    RecipeCreateUpdateSerializer
)
from .permissions import IsOwnerOrReadOnly, IsAuthenticatedOrCreateReadOnly
from recipes.models import (
    Tag,
    Ingredient,
    Recipe,
    Favorite,
    ShoppingCart,
    Subscription
)

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
            response_serializer = UserSerializer(
                user,
                context={'request': request}
            )
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

        if request.method == 'DELETE':
            if user.avatar:
                try:
                    user.avatar.delete(save=False)
                except Exception:
                    pass

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

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='subscribe'
    )
    def subscribe(self, request, pk=None):
        """
        Подписка на автора:
        - POST /api/users/{id}/subscribe - подписаться;
        - DELETE /api/users/{id}/subscribe - отписаться.
        """
        author = self.get_object()
        user = request.user

        if user == author:
            return Response(
                {'error': 'Нельзя подписать на себя'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.method == 'POST':
            subscription, created = Subscription.objects.get_or_create(
                user=user,
                author=author
            )

            if not created:
                return Response(
                    {'error': 'Уже подписан.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = UserSerializer(author, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            try:
                subscription = Subscription.objects.get(
                    user=user, author=author)
                subscription.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Subscription.DoesNotExist:
                return Response(
                    {'error': 'Подписка не найдена'},
                    status=status.HTTP_400_BAD_REQUEST
                )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='subscriptions'
    )
    def subscriptions(self, request):
        """
        Список подписок пользователя:
        - GET /api/users/subscriptions.
        """
        subscriptions = Subscription.objects.filter(user=request.user)
        authors = User.objects.filter(id__in=subscriptions.values('author'))

        page = self.paginate_queryset(authors)
        if page is not None:
            serializer = UserWithRecipesSerializer(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = UserWithRecipesSerializer(
            authors, many=True, context={'request': request})
        return Response(serializer.data)


class CustomAuthToken(ObtainAuthToken):
    """
    Идентификация и аутентификация пользователя.
    """
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')

        if email and password:
            try:
                user = User.objects.get(email=email)
                user = authenticate(username=user.username, password=password)
                if user:
                    token, created = Token.objects.get_or_create(user=user)
                    return Response({'auth_token': token.key})
            except User.DoesNotExist:
                pass

        return Response(
            {
                'non_field_errors': [
                    'Unable to log in with provided credentials.'
                ]
            },
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        request.user.auth_token.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except Token.DoesNotExist:
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        """Фильтрация ингредиентов по имени."""
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')

        if name:
            queryset = queryset.filter(name__istartswith=name)

        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для рецептов."""
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия."""
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateUpdateSerializer
        return RecipeSerializer

    def get_queryset(self):
        """Фильтрация рецептов."""
        queryset = Recipe.objects.all()

        author = self.request.query_params.get('author')
        if author:
            queryset = queryset.filter(author=author)

        tags = self.request.query_params.getlist('tags')
        if tags:
            queryset = queryset.filter(tags__slug__in=tags).distinct()

        is_favorited = self.request.query_params.get('is_favorited')
        if is_favorited and self.request.user.is_authenticated:
            if is_favorited == '1':
                queryset = queryset.filter(
                    favorite__user=self.request.user
                )

        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart')
        if is_in_shopping_cart and self.request.user.is_authenticated:
            if is_in_shopping_cart == '1':
                queryset = queryset.filter(
                    shoppingcart__user=self.request.user
                )

        return queryset

    def perform_create(self, serializer):
        """Автоматически устанавливаем автора при создании."""
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='favorite'
    )
    def favorite(self, request, pk=None):
        """
        Работа с избранными рецептами:
        - POST /api/recipes/{id}/favorite/ - добавить;
        - DELETE /api/recipes/{id}/favorite/ - удалить.
        """
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            favorite, created = Favorite.objects.get_or_create(
                user=user,
                recipe=recipe
            )

            if not created:
                return Response(
                    {'error': 'Рецепт уже в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response({
                'id': recipe.id,
                'name': recipe.name,
                'image': recipe.image.url if recipe.image else None,
                'cooking_time': recipe.cooking_time
            }, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            try:
                favorite = Favorite.objects.get(user=user, recipe=recipe)
                favorite.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Favorite.DoesNotExist:
                return Response(
                    {'error': 'Рецепт не в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='shopping_cart'
    )
    def shopping_cart(self, request, pk=None):
        """
        Работа с корзиной:
        - POST /api/recipes/{id}/shopping_cart/ - добавить;
        - DELETE /api/recipes/{id}/shopping_cart/ - удалить.
        """
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            shopping_cart, created = ShoppingCart.objects.get_or_create(
                user=user,
                recipe=recipe
            )

            if not created:
                return Response(
                    {'error': 'Рецепт уже в корзине'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response({
                'id': recipe.id,
                'name': recipe.name,
                'image': recipe.image.url if recipe.image else None,
                'cooking_time': recipe.cooking_time
            }, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            try:
                shopping_cart = ShoppingCart.objects.get(
                    user=user, recipe=recipe)
                shopping_cart.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except ShoppingCart.DoesNotExist:
                return Response(
                    {'error': 'Рецепт не в корзине'},
                    status=status.HTTP_400_BAD_REQUEST
                )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='download_shopping_cart'
    )
    def download_shopping_cart(self, request):
        """Скачивание списка покупок в виде текстового файла."""
        shopping_cart_recipes = Recipe.objects.filter(
            shoppingcart__user=request.user
        ).prefetch_related('recipeingredient_set__ingredient')

        ingredients_dict = {}

        for recipe in shopping_cart_recipes:
            for recipe_ingredient in recipe.recipeingredient_set.all():
                ingredient = recipe_ingredient.ingredient
                key = f"{ingredient.name} ({ingredient.measurement_unit})"

                if key in ingredients_dict:
                    ingredients_dict[key] += recipe_ingredient.amount
                else:
                    ingredients_dict[key] = recipe_ingredient.amount

        content = "Список покупок:\n\n"
        for ingredient, amount in ingredients_dict.items():
            content += f"• {ingredient}: {amount}\n"

        response = HttpResponse(
            content, content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = 'attachment; ' \
            'filename="shopping_list.txt"'
        return response

    @action(
        detail=True,
        methods=['get'],
        permission_classes=[AllowAny],
        url_path='get-link'
    )
    def get_link(self, request, pk=None):
        """Получение короткой ссылки на рецепт."""
        recipe = self.get_object()

        short_link = f"{request.build_absolute_uri('/')[:-1]}/s/{recipe.id}/"

        return Response({
            'short-link': short_link
        })
