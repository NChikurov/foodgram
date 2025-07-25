from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

from api.validators import validate_name_format


class User(AbstractUser):
    """
    Расширенная модель пользователя.
    """
    username = models.CharField(
        'Никнейм',
        max_length=150,
        validators=[UnicodeUsernameValidator()],
    )
    first_name = models.CharField(
        'Имя',
        max_length=30,
        validators=[validate_name_format]
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=30,
        validators=[validate_name_format]
    )
    email = models.CharField('Почта', max_length=254, unique=True)
    avatar = models.ImageField(
        'Аватар',
        upload_to='users/avatars',
        blank=True,
        null=True,
        help_text='Загрузите фото профиля'
    )

    class Meta:
        ordering = ('id',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username
