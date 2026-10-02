from django import forms
from urllib.parse import urlparse
from .models import TrackedTeam


class AddTrackedTeamForm(forms.Form):
    url = forms.URLField(
        label="Ссылка на страницу команды (volleypgo.ru)",
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://volleypgo.ru/teams/petrgu-men/',
            'required': True
        })
    )

    def clean_url(self):
        url = self.cleaned_data['url'].strip()
        parsed = urlparse(url)

        if 'volleypgo.ru' not in parsed.netloc or '/teams/' not in parsed.path:
            raise forms.ValidationError(
                "Укажите корректную ссылку на команду с сайта volleypgo.ru (например, https://volleypgo.ru/teams/petrgu-men/)")

        return url


class GameFilterForm(forms.Form):
    team = forms.ModelChoiceField(
        queryset=TrackedTeam.objects.none(),
        required=False,
        label="Команда",
        empty_label="Все отслеживаемые команды",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        required=False,
        label="Дата с",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'lang': 'ru'})
    )
    date_to = forms.DateField(
        required=False,
        label="Дата по",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and user.is_authenticated:
            # Ограничиваем список команд только теми, которые отслеживает текущий пользователь
            self.fields['team'].queryset = user.tracked_teams.all()
