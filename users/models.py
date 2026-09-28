from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class CustomUser(AbstractUser):
    birth_date = models.DateField(null=True, blank=True)

    def clean(self):
        # Обязательно вызываем родительский метод clean
        super().clean()

        if self.username:
            username_exists = ReservedName.objects.filter(
                username=self.username
            ).exists()

            if username_exists:
                raise ValidationError({
                    'username': "Данный никнейм зарегистрирован"
                })

    def __str__(self):
        return self.username


class ReservedName(models.Model):
    username = models.CharField(max_length=150, unique=True, verbose_name="Зарезервированный никнейм")

    class Meta:
        verbose_name = "Зарезервированный никнейм"
        verbose_name_plural = "Зарезервированные никнеймы"

    def __str__(self):
        return self.username
