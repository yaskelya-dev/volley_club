from django import forms
from django.db.models import Q
from .models import Training, AbsenceReason
from teams.models import Team


class TrainingForm(forms.ModelForm):
    """Форма создания тренировки"""
    class Meta:
        model = Training
        fields = ['team', 'date']
        widgets = {
            'team': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
        labels = {
            'team': 'Команда',
            'date': 'Дата тренировки',
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            # Показываем только команды текущего пользователя
            self.fields['team'].queryset = Team.objects.filter(owner=user).order_by('title')


class AbsenceReasonForm(forms.ModelForm):
    """Форма создания пользовательской причины пропуска"""
    class Meta:
        model = AbsenceReason
        fields = ['title']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: Соревнования',
                'autocomplete': 'off'
            })
        }
        labels = {
            'title': 'Название причины'
        }
