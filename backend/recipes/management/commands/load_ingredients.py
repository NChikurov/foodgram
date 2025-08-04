import json

from django.core.management.base import BaseCommand
from recipes.models import Ingredient

class Command(BaseCommand):
    help = 'Загружает ингредиенты из JSON файла'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='ingredients.json',
            help='Путь к JSON файлу с ингредиентами'
        )

    def handle(self, *args, **options):
        file_path = options['file']

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                ingredients_data = json.load(file)

            ingredients_to_create = []

            for ingredient_data in ingredients_data:
                name = ingredient_data['name']
                if not Ingredient.objects.filter(name=name).exists():
                    ingredients_to_create.append(
                        Ingredient(
                            name=name,
                            measurement_unit=ingredient_data[
                                'measurement_unit'
                            ]
                        )
                    )

            if ingredients_to_create:
                Ingredient.objects.bulk_create(ingredients_to_create)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Успешно загружено {len(ingredients_to_create)} '
                        f'ингредиентов'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING('Все ингредиенты уже существуют')
                )

        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'Файл {file_path} не найден')
            )
        except json.JSONDecodeError:
            self.stdout.write(
                self.style.ERROR('Ошибка декодирования JSON файла')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка: {str(e)}')
            )
