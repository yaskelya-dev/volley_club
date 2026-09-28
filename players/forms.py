from django import forms
from .models import Player


class PlayerForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите ФИО игрока',
                'autocomplete': 'off'
            })
        }
        labels = {
            'name': 'ФИО игрока'
        }
