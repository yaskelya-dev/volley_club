from django.db import models
from volley_club import settings


class TrackedTeam(models.Model):
    url = models.URLField("Ссылка на команду", unique=True, max_length=500)
    name = models.CharField("Название команды", max_length=255)
    league = models.CharField("Лига/Дивизион", max_length=255, blank=True, null=True)
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="tracked_teams",
        verbose_name="Отслеживающие пользователи",
        blank=True
    )
    last_updated = models.DateTimeField("Дата последнего обновления", auto_now=True)

    class Meta:
        verbose_name = "Отслеживаемая команда"
        verbose_name_plural = "Отслеживаемые команды"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.league or 'Без лиги'})"


class Game(models.Model):
    class GameStatus(models.TextChoices):
        UPCOMING = 'upcoming', 'Предстоящая'
        COMPLETED = 'completed', 'Завершённая'

    team = models.ForeignKey(TrackedTeam, on_delete=models.CASCADE, related_name="games", verbose_name="Команда")
    status = models.CharField("Статус игры", max_length=20, choices=GameStatus.choices, default=GameStatus.UPCOMING)

    matchup_text = models.CharField("Матч / Вывеска", max_length=255)  # Например: "ПТЗ — ПетрГУ"
    date_str = models.CharField("Дата и время", max_length=100)  # Например: "4 октября 2026 г., 20:00"
    score = models.CharField("Счет", max_length=50, blank=True, null=True)  # Например: "3 : 1"

    class Meta:
        verbose_name = "Игра"
        verbose_name_plural = "Игры"
        ordering = ['id']

    def __str__(self):
        return f"{self.matchup_text} [{self.date_str}]"
