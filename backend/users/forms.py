from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    """
    Класс для переопределения модели, с которой работает форма.
    """
    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            'first_name',
            'last_name',
            'username',
            'email',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True


class CustomUserChangeForm(UserChangeForm):
    """
    Форма для изменения пользователей в админке.
    """
    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'username',
            'email',
            'avatar',
            'is_active',
            'is_staff',
            'is_superuser',
        )
