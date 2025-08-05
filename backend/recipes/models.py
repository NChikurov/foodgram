from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from .constants import (MAX_COOKING_TIME, MAX_INGREDIENT_AMOUNT,
                        MIN_COOKING_TIME, MIN_INGREDIENT_AMOUNT)

User = get_user_model()


class Tag(models.Model):
    """
    Теги для рецептов.
    """
    name = models.CharField('Название тега', max_length=200)
    slug = models.SlugField('Слаг', unique=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """
    Ингредиенты для рецептов.
    """
    name = models.CharField('Ингредиент', max_length=200)
    measurement_unit = models.CharField('Единица измерения', max_length=50)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """
    Рецепт блюда.
    """
    name = models.CharField('Название рецепта', max_length=256)
    text = models.TextField('Описание рецепта')
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления мин.',
        validators=[
            MinValueValidator(
                MIN_COOKING_TIME,
                message=(f'Время приготовления не может быть меньше '
                         f'{MIN_COOKING_TIME} минуты')
            ),
            MaxValueValidator(
                MAX_COOKING_TIME,
                message=(f'Время приготовления не может быть больше '
                         f'{MAX_COOKING_TIME} минут')
            )
        ]
    )
    image = models.ImageField(
        'Фото рецепта',
        upload_to='recipes/images',
        help_text='Загрузите фото рецепта'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='recipes'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты')
    tags = models.ManyToManyField(Tag, verbose_name='Тег')

    class Meta:
        ordering = ('-id',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """
    Ингредиенты в конкретном рецепте.
    """
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients'
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=[
            MinValueValidator(
                MIN_INGREDIENT_AMOUNT,
                message=(f'Количество не может быть меньше '
                         f'{MIN_INGREDIENT_AMOUNT}')
            ),
            MaxValueValidator(
                MAX_INGREDIENT_AMOUNT,
                message=(f'Количество не может быть больше '
                         f'{MAX_INGREDIENT_AMOUNT}')
            )
        ]
    )

    class Meta:
        ordering = ('recipe', 'ingredient')
        unique_together = ('recipe', 'ingredient')
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'

    def __str__(self):
        return f'{self.recipe.name} - {self.ingredient.name}'


class Favorite(models.Model):
    """
    Любимые рецепты пользователя.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorited_by'
    )

    class Meta:
        ordering = ('-id',)
        unique_together = ('user', 'recipe')
        verbose_name = 'Любимый рецепт'
        verbose_name_plural = 'Любимые рецепты'

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'


class ShoppingCart(models.Model):
    """
    Корзина покупок пользователя.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_shopping_cart'
    )

    class Meta:
        ordering = ('-id',)
        unique_together = ('user', 'recipe')
        verbose_name = 'Корзина покупок'
        verbose_name_plural = 'Корзина покупок'

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'


class Subscription(models.Model):
    """
    Подписки на авторов рецептов.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following'
    )

    class Meta:
        ordering = ('-id',)
        unique_together = ('user', 'author')
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.user.username} -> {self.author.username}'
