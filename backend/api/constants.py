"""
Константы для валидации данных в API.
"""

# Валидация количества ингредиентов
MIN_INGREDIENT_AMOUNT = 1
MAX_INGREDIENT_AMOUNT = 32000

# Валидация времени приготовления (в минутах)
MIN_COOKING_TIME = 1
MAX_COOKING_TIME = 32000

# Валидация длины текстовых полей
MIN_NAME_LENGTH = 2
MAX_NAME_LENGTH = 256
MAX_USERNAME_LENGTH = 150

MIN_TEXT_LENGTH = 1
MAX_TEXT_LENGTH = 10000

# Валидация пароля
MIN_PASSWORD_LENGTH = 8

# Валидация количества тегов и ингредиентов
MIN_TAGS_COUNT = 1
MIN_INGREDIENTS_COUNT = 1

# Лимиты для отображения
DEFAULT_RECIPES_LIMIT = 3
MAX_RECIPES_LIMIT = 100

# Значения фильтров
FAVORITE_TRUE = '1'
SHOPPING_CART_TRUE = '1'
