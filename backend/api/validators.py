import re

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .constants import (MIN_NAME_LENGTH, MIN_PASSWORD_LENGTH,
                        MAX_USERNAME_LENGTH)

User = get_user_model()


def validate_unique_email(value):
    """Проверяет уникальность email."""
    if User.objects.filter(email=value).exists():
        raise serializers.ValidationError(
            'Пользователь с таким email уже существует.'
        )

    return value


def validate_unique_email_update(value, instance):
    """Проверяет уникальность email при обновлении."""
    if User.objects.filter(email=value).exclude(pk=instance.pk).exists():
        raise serializers.ValidationError(
            'Пользователь с таким email уже существует.'
        )
    return value


def validate_unique_username(value):
    """Проверяет уникальность никнейма."""
    if User.objects.filter(username=value).exists():
        raise serializers.ValidationError(
            'Пользователь с таким никнеймом уже существует.'
        )

    return value


def validate_username_format(value):
    """Проверяет формат username согласно Django стандартам."""
    if len(value) > MAX_USERNAME_LENGTH:
        raise serializers.ValidationError(
            f'Username не может быть длиннее '
            f'{MAX_USERNAME_LENGTH} символов.'
        )

    if not re.match(r'^[\w.@+-]+$', value):
        raise serializers.ValidationError(
            'Username может содержать только буквы, цифры и '
            'символы @/./+/-/_'
        )

    return value


def validate_unique_username_update(value, instance):
    """Проверяет уникальность username при обновлении."""
    if User.objects.filter(username=value).exclude(pk=instance.pk).exists():
        raise serializers.ValidationError(
            'Пользователь с таким никнеймом уже существует.'
        )
    return value


def validate_password_strength(value):
    """Проверяет сложность пароля."""
    if value.isdigit():
        raise serializers.ValidationError(
            'Пароль не может состоять только из цифр.'
        )

    if len(value) < MIN_PASSWORD_LENGTH:
        raise serializers.ValidationError(
            f'Пароль должен состоять минимум из '
            f'{MIN_PASSWORD_LENGTH} символов'
        )

    if value.lower() == value:
        raise serializers.ValidationError(
            'Пароль должен содержать хотя бы одну заглавную букву.'
        )

    return value


def validate_name_format(value):
    """Проверяет формат имени и фамилии."""
    if not value.strip():
        raise serializers.ValidationError(
            'Поле не может быть пустым.'
        )

    if len(value) < MIN_NAME_LENGTH:
        raise serializers.ValidationError(
            f'Имя (фамилия) должно содержать минимум '
            f'{MIN_NAME_LENGTH} символа.'
        )

    if not value.replace(' ', '').replace('-', '').isalpha():
        raise serializers.ValidationError(
            'Имя может содержать только буквы, пробелы и дефис.'
        )

    return value.strip().title()
