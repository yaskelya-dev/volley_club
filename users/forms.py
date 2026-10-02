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


class UserProfileForm(forms.ModelForm):
    telegram_username = forms.CharField(
        max_length=32,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'username (без @)'
        }),
        label="Telegram Username"
    )

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'birth_date', 'telegram_username']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Имя'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Фамилия'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'birth_date': 'Дата рождения',
        }

    def clean_telegram_username(self):
        username = self.cleaned_data.get('telegram_username')
        if username:
            # Убираем символ @ в начале, если пользователь случайно ввел его
            username = username.strip().lstrip('@')
        return username


class TelegramVerifyCodeForm(forms.Form):
    code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg text-center letter-spacing-2',
            'placeholder': '123456',
            'autocomplete': 'off',
            'autofocus': 'autofocus'
        }),
        label="Код подтверждения"
    )
