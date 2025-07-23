from django.contrib import admin
from django contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User
from .forms import CustomUserCreationForm, CustomUserChangeForm


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Стандартная админка.
    """
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User

    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'is_staff'
    )
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Дополнительная информация', {'fields': ('avatar',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username',
                       'first_name',
                       'last_name',
                       'email',
                       'password'                  
                    ),
        })
    )
    
