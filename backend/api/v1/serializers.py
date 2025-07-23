from rest_framework import serializers

from django.contrib.auth import get_user_model

from .validators import (
    validate_unique_email,
    validate_unique_username,
    validate_password_strength,
    validate_name_format
)


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для отображения пользователей.
    Используется для GET-запросов.
    """
    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'avatar'
        )
        read_only_fields = ('id',)


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
        validators=[validate_unique_username]
    )
    email = serializers.CharField(
        validators = [validate_unique_email]
    )
    first_name = serializers.CharField(
        validators = [validate_name_format]
    )
    last_name = serializers.CharField(
        validators = [validate_name_format]
    )

    class Meta:
        model = User
        fields = (
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
        validators = [validate_name_format]
    )
    last_name = serializers.CharField(
        validators = [validate_name_format]
    )

    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'avatar'
        )

    def update(self, instance, validated_data):
        """Обновляем только разрешенные поля."""
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.avatar = validated_data.get('avatar', instance.avatar)
        instance.save()
        return instance
