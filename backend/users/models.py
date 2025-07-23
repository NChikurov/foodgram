from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Расширенная модель пользователя.
    """
    first_name = models.CharField('Имя', max_length=30)
    last_name = models.CharField('Фамилия', max_length=30)
    email = models.CharField('Почта', max_length=100, unique=True)
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
