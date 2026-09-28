from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    # Поля, по которым можно будет сортировать в списке (нажатием на заголовок колонки)
    ordering = ['username']  # Сортировка по умолчанию в админке

    # Добавляем birth_date в список отображаемых полей
    list_display = ['username', 'email', 'first_name', 'last_name', 'birth_date', 'is_staff']

    # Добавляем фильтры в правую колонку (удобно для дат и статусов)
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'birth_date']

    # Добавляем поле birth_date в формы редактирования пользователя в админке
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {'fields': ('birth_date',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Дополнительная информация', {'fields': ('birth_date',)}),
    )
