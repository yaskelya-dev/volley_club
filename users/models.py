import random
from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class CustomUser(AbstractUser):
    birth_date = models.DateField(null=True, blank=True)
    telegram_username = models.CharField(
        max_length=32, null=True, blank=True, verbose_name="Telegram Username"
    )
    telegram_id = models.BigIntegerField(
        null=True, blank=True, unique=True, verbose_name="Telegram ID"
    )
    is_telegram_verified = models.BooleanField(
        default=False, verbose_name="Telegram подтвержден"
    )

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


def one_hour_hence():
    return timezone.now() + timedelta(hours=1)


class TelegramVerificationCode(models.Model):
    """Временные коды подтверждения для привязки Telegram"""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='tg_code')
    code = models.CharField(max_length=6)
    expires_at = models.DateTimeField(default=one_hour_hence)

    def generate_code(self):
        self.code = str(random.randint(100000, 999999))
        self.save()
        return self.code


class ReservedName(models.Model):
    username = models.CharField(max_length=150, unique=True, verbose_name="Зарезервированный никнейм")

    class Meta:
        verbose_name = "Зарезервированный никнейм"
        verbose_name_plural = "Зарезервированные никнеймы"

    def __str__(self):
        return self.username
