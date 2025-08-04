from django.contrib import admin

from .models import (Favorite, Ingredient, Recipe, ShoppingCart, Subscription,
                     Tag)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Администрирование справочника тегов."""
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Администрирование справочника ингредиентов."""
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Администрирование справочника рецептов."""
    list_display = (
        'name',
        'cooking_time',
        'author',
        'get_tags_display',
        'get_ingredients_count',
    )
    list_filter = ('tags', 'cooking_time', 'author',)
    search_fields = (
        'name',
        'author__username',
    )
    filter_horizontal = ('tags',)

    def get_tags_display(self, obj):
        return ', '.join([tag.name for tag in obj.tags.all()])
    get_tags_display.short_description = 'Теги'

    def get_ingredients_count(self, obj):
        return obj.ingredients.count()
    get_ingredients_count.short_description = 'Кол-во ингредиентов'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Администраирование справочника избранного."""
    list_display = ('user', 'recipe', 'get_recipe_author')
    list_filter = ('recipe__author',)
    search_fields = (
        'user__username',
        'recipe__name',
    )

    def get_recipe_author(self, obj):
        return obj.recipe.author
    get_recipe_author.short_description = 'Автор рецепта'


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe', 'get_recipe_author')
    list_filter = ('recipe__author',)
    search_fields = (
        'user__username',
        'recipe__name',
    )

    def get_recipe_author(self, obj):
        return obj.recipe.author
    get_recipe_author.short_description = 'Автор рецепта'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Администрирование подписок пользователей."""
    list_display = ('user', 'author', 'get_author_recipes_count')
    list_filter = ('author',)
    search_fields = (
        'user__username',
        'author__username',
        'author__first_name',
        'author__last_name',
    )

    def get_author_recipes_count(self, obj):
        """Показывает количество рецептов автора."""
        return obj.author.recipe_set.count()
    get_author_recipes_count.short_description = 'Рецептов у автора'
