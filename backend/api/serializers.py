import base64
import binascii
import uuid

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from rest_framework import serializers

from recipes.models import (Ingredient, Recipe, RecipeIngredient,
                            Subscription, Tag)

from .constants import (DEFAULT_RECIPES_LIMIT, MAX_INGREDIENT_AMOUNT,
                        MIN_INGREDIENT_AMOUNT, MIN_COOKING_TIME,
                        MIN_INGREDIENTS_COUNT, MIN_TAGS_COUNT)
from .validators import (validate_name_format, validate_password_strength,
                         validate_unique_email, validate_unique_email_update,
                         validate_unique_username, validate_username_format)

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

        return request.user.follower.filter(author=obj).exists()


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
            recipes_limit = DEFAULT_RECIPES_LIMIT

        recipes = obj.recipes.all()[:recipes_limit]

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
        return obj.recipes.count()


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


class ChangePasswordSerializer(serializers.Serializer):
    """Сериализатор для смены пароля."""
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password_strength]
    )

    def validate_current_password(self, value):
        """Валидация текущего пароля."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Неверный пароль')
        return value

    def validate(self, data):
        """Валидация всех данных."""
        current_password = data.get('current_password')
        new_password = data.get('new_password')

        if not current_password:
            raise serializers.ValidationError({
                'current_password': 'Обязательное поле'
            })

        if not new_password:
            raise serializers.ValidationError({
                'new_password': 'Обязательное поле'
            })

        return data

    def save(self):
        """Сохранение нового пароля."""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class SubscriptionSerializer(serializers.Serializer):
    """Сериализатор для подписок."""

    def validate(self, data):
        """Валидация подписки."""
        request = self.context['request']
        author = self.context['author']
        user = request.user

        if user == author:
            raise serializers.ValidationError('Нельзя подписаться на себя')

        if user.follower.filter(author=author).exists():
            raise serializers.ValidationError('Уже подписан')

        return data

    def save(self):
        """Создание подписки."""
        request = self.context['request']
        author = self.context['author']
        user = request.user

        subscription = Subscription.objects.create(
            user=user,
            author=author
        )
        return subscription


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
    amount = serializers.IntegerField(
        min_value=MIN_INGREDIENT_AMOUNT,
        max_value=MAX_INGREDIENT_AMOUNT
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов."""
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredients',
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

        return request.user.favorites.filter(recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        """Проверяет, добавлен ли рецепт в корзину."""
        request = self.context.get('request')

        if not request or not request.user.is_authenticated:
            return False

        return request.user.shopping_cart.filter(recipe=obj).exists()


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецептов."""
    ingredients = RecipeIngredientCreateSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(min_value=MIN_COOKING_TIME)

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
        return self.validate_empty(data)

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
                'ingredients': (
                    f'Нужен хотя бы {MIN_INGREDIENTS_COUNT} ингредиент'
                )
            })

        if 'tags' in data and not data['tags']:
            raise serializers.ValidationError({
                'tags': f'Нужен хотя бы {MIN_TAGS_COUNT} тег'
            })

        return data

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
            instance.recipe_ingredients.all().delete()
            self.create_ingredients(instance, ingredients_data)

        return instance

    def to_representation(self, instance):
        """Возвращаем полное представление рецепта."""
        return RecipeSerializer(
            instance,
            context=self.context
        ).data
