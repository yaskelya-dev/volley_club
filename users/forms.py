from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Автоматически добавляем Bootstrap класс 'form-control' ко всем полям
        for field_name, field in self.fields.items():
            if field_name != 'birth_date':
                field.widget.attrs['class'] = 'form-control'


class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляем Bootstrap классы для полей username и password
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
