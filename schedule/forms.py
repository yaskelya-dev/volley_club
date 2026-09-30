from django import forms
from urllib.parse import urlparse


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
