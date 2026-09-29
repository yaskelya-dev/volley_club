from django import forms
from .models import Team, TeamPlayer
from players.models import Player


class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['title']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название команды',
                'autocomplete': 'off'
            })
        }
        labels = {
            'title': 'Название команды'
        }


class TeamPlayerAddForm(forms.ModelForm):
    class Meta:
        model = TeamPlayer
        fields = ['player', 'number']
        widgets = {
            'player': forms.Select(attrs={'class': 'form-select'}),
            'number': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '№',
                'min': 1,
                'max': 99
            }),
        }
        labels = {
            'player': 'Выберите игрока',
            'number': 'Игровой номер'
        }

    def __init__(self, *args, user=None, team=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and team:
            # Исключаем игроков, которые уже состоят в этой команде
            in_team_player_ids = team.players.values_list('id', flat=True)
            self.fields['player'].queryset = Player.objects.filter(
                created_by=user
            ).exclude(id__in=in_team_player_ids).order_by('name')
