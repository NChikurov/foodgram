from rest_framework import serializers

from django.contrib.auth import get_user_model

from recipes.models import (
    Tag,
    Ingredient,
    Recipe,
    RecipeIngredient,
)
from .validators import (
    validate_unique_email,
    validate_unique_email_update,
    validate_unique_username,
    validate_password_strength,
    validate_name_format,
    validate_username_format
)


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для отображения пользователей.
    Используется для GET-запросов.
    """
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_subscribed',
            'avatar',
            'recipes',
            'recipes_count'
        )
        read_only_fields = ('id',)

    def get_is_subscribed(self, obj):
        """
        Проверяем, подписан ли текущий пользователь на другого.
        """
        request = self.context.get('request')

        if request and request.user.is_authenticated:
            return False

        return False

    def get_recipes(self, obj):
        """Возвращает рецепты автора."""
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit', 3)

        try:
            recipes_limit = int(recipes_limit)
        except (ValueError, TypeError):
            recipes_limit = 3

        recipes = obj.recipe_set.all()[:recipes_limit]

        return [
            {
                'id': recipe.id,
                'name': recipe.name,
                'image': recipe.image.url if recipe.image else None,
                'cooking_time': recipe.cooking_time
            }
            for recipe in recipes
        ]

    def get_recipes_count(self, obj):
        """Возвращает общее количество рецептов автора."""
        return obj.recipe_set.count()


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для регистрации пользователей.
    Используется для POST-запросов.
    """
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password_strength]
    )
    username = serializers.CharField(
        validators=[validate_unique_username, validate_username_format]
    )
    email = serializers.EmailField(
        validators=[validate_unique_email]
    )
    first_name = serializers.CharField(
        validators=[validate_name_format]
    )
    last_name = serializers.CharField(
        validators=[validate_name_format]
    )

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'password'
        )

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для обновления профиля пользователя.
    Используется для PUT/PATCH запросов.
    """
    first_name = serializers.CharField(
        validators=[validate_name_format]
    )
    last_name = serializers.CharField(
        validators=[validate_name_format]
    )
    email = serializers.EmailField(required=False)

    class Meta:
        model = User
        fields = (
            'email',
            'first_name',
            'last_name',
            'avatar'
        )

    def validate_email(self, value):
        if value:
            return validate_unique_email_update(value, self.instance)
        return value

    def update(self, instance, validated_data):
        """Обновляем только разрешенные поля."""
        instance.first_name = validated_data.get(
            'first_name', instance.first_name)
        instance.last_name = validated_data.get(
            'last_name', instance.last_name)
        instance.avatar = validated_data.get('avatar', instance.avatar)
        instance.save()
        return instance


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')
        read_only_fields = ('id',)


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = ('id',)


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов в рецепте."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов."""
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipeingredient_set',
        many=True,
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )
        read_only_fields = ('id', 'author')

    def get_is_favorited(self, obj):
        """Проверяет, добавлен ли рецепт в избранное."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False

        from recipes.models import Favorite

        return Favorite.objects.filter(
            user=request.user,
            recipe=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        """Проверяет, добавлен ли рецепт в корзину."""
        request = self.context.get('request')

        if not request or not request.user.is_authenticated:
            return False

        from recipes.models import ShoppingCart

        return ShoppingCart.objects.filter(
            user=request.user,
            recipe=obj
        ).exists()
