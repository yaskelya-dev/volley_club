from django.db import models
from volley_club import settings


class Player(models.Model):
    name = models.CharField(max_length=100, verbose_name="ФИО игрока")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_players",
        verbose_name="Кто создал"
    )

    class Meta:
        verbose_name = "Игрок"
        verbose_name_plural = "Игроки"

    def __str__(self):
        return self.name
