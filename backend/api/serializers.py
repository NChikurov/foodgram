import base64
import binascii

import uuid

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from rest_framework import serializers

from recipes.models import (
    Tag,
    Ingredient,
    Recipe,
    RecipeIngredient,
    Subscription
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


class Base64ImageField(serializers.ImageField):
    """
    Поле для обработки изображений в формате base64.
    """
    def to_internal_value(self, data):
        if hasattr(data, 'read'):
            return super().to_internal_value(data)

        if isinstance(data, str):
            if 'data:' in data and ';base64,' in data:
                header, data = data.split(';base64,')

                try:
                    decoded_file = base64.b64decode(data)
                except (ValueError, TypeError, binascii.Error):
                    raise serializers.ValidationError('Неверный формат base64')

                file_extension = 'jpg'
                if 'png' in header:
                    file_extension = 'png'
                elif 'gif' in header:
                    file_extension = 'gif'

                file_name = f"{uuid.uuid4()}.{file_extension}"

                data = ContentFile(decoded_file, name=file_name)

                return super().to_internal_value(data)

        return super().to_internal_value(data)


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для отображения пользователей.
    Используется для GET-запросов.
    """
    is_subscribed = serializers.SerializerMethodField()

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
        )
        read_only_fields = ('id',)

    def get_is_subscribed(self, obj):
        """
        Проверяем, подписан ли текущий пользователь на другого.
        """
        request = self.context.get('request')

        if not request or not request.user.is_authenticated:
            return False

        return Subscription.objects.filter(
            user=request.user,
            author=obj
        ).exists()


class UserWithRecipesSerializer(UserSerializer):
    """Сериализатор для вывода рецептов пользователя."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')

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
    avatar = Base64ImageField(required=False, allow_null=True)

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


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания ингредиентов в рецепте."""
    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


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


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецептов."""
    ingredients = RecipeIngredientCreateSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time'
        )

    def validate(self, data):
        """
        Валидация всех данных.
        """
        data = self.validate_empty(data)
        return data

    def validate_empty(self, data):
        """
        Проверка обязательных полей.
        """
        request = self.context.get('request')

        if request and request.method in ['PUT', 'PATCH']:
            if 'ingredients' not in data:
                raise serializers.ValidationError({
                    'ingredients': 'Это поле обязательно.'
                })

            if 'tags' not in data:
                raise serializers.ValidationError({
                    'tags': 'Это поле обязательно.'
                })

        if 'ingredients' in data and not data['ingredients']:
            raise serializers.ValidationError({
                'ingredients': 'Нужен хотя бы один ингредиент'
            })

        if 'tags' in data and not data['tags']:
            raise serializers.ValidationError({
                'tags': 'Нужен хотя бы один тег'
            })

        return data

    def validate_ingredients(self, value):
        """Валидация ингредиентов."""
        if not value:
            raise serializers.ValidationError(
                'Нужен хотя бы один ингредиент'
            )

        ingredient_ids = [item['id'] for item in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться'
            )

        existing_ingredients = Ingredient.objects.filter(
            id__in=ingredient_ids
        )
        if len(existing_ingredients) != len(ingredient_ids):
            raise serializers.ValidationError(
                'Указан несуществующий ингредиент'
            )

        return value

    def validate_tags(self, value):
        """Валидация тегов."""
        if not value:
            raise serializers.ValidationError(
                'Нужен хотя бы один тег'
            )

        if len(value) != len(set(value)):
            raise serializers.ValidationError(
                'Теги не должны повторяться'
            )

        return value

    def validate_name(self, value):
        """Валидация названия."""
        if not value or not value.strip():
            raise serializers.ValidationError(
                'Название не может быть пустым'
            )
        return value.strip()

    def validate_text(self, value):
        """Валидация описания."""
        if not value or not value.strip():
            raise serializers.ValidationError(
                'Описание не может быть пустым'
            )
        return value.strip()

    def validate_image(self, value):
        """Валидация изображения."""
        if not value:
            raise serializers.ValidationError(
                'Изображение обязательно'
            )
        return value

    def create_ingredients(self, recipe, ingredients_data):
        """Создание ингредиентов для рецепта."""
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=ingredient_data['id'],
                amount=ingredient_data['amount']
            )
            for ingredient_data in ingredients_data
        ])

    def create(self, validated_data):
        """Создание рецепта."""
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        self.create_ingredients(recipe, ingredients_data)

        return recipe

    def update(self, instance, validated_data):
        """Обновление рецепта."""
        ingredients_data = validated_data.pop('ingredients', None)
        tags_data = validated_data.pop('tags', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if tags_data is not None:
            instance.tags.set(tags_data)

        if ingredients_data is not None:
            instance.recipeingredient_set.all().delete()
            self.create_ingredients(instance, ingredients_data)

        return instance

    def to_representation(self, instance):
        """Возвращаем полное представление рецепта."""
        return RecipeSerializer(
            instance,
            context=self.context
        ).data
