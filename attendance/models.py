from django.db import models
from volley_club import settings
from teams.models import Team
from players.models import Player


class AbsenceReason(models.Model):
    title = models.CharField(max_length=100, verbose_name="Причина пропуска")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="absence_reasons",
        verbose_name="Кто создал"
    )
    is_default = models.BooleanField(default=False, verbose_name="Системная причина")

    class Meta:
        verbose_name = "Причина пропуска"
        verbose_name_plural = "Причины пропусков"
        ordering = ['-is_default', 'title']

    def __str__(self):
        return self.title


class Training(models.Model):
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="trainings",
        verbose_name="Команда"
    )
    date = models.DateField(verbose_name="Дата тренировки")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="trainings",
        verbose_name="Кто создал"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Тренировка"
        verbose_name_plural = "Тренировки"
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"Тренировка {self.team.title} ({self.date.strftime('%d.%m.%Y')})"


class AttendanceRecord(models.Model):
    training = models.ForeignKey(
        Training,
        on_delete=models.CASCADE,
        related_name="records",
        verbose_name="Тренировка"
    )
    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name="attendance_records",
        verbose_name="Игрок"
    )
    is_present = models.BooleanField(default=True, verbose_name="Присутствовал")
    reason = models.ForeignKey(
        AbsenceReason,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Причина пропуска"
    )

    class Meta:
        verbose_name = "Запись посещаемости"
        verbose_name_plural = "Записи посещаемости"
        unique_together = ('training', 'player')

    def __str__(self):
        status = "Был" if self.is_present else f"Отсутствовал ({self.reason})"
        return f"{self.player.name} — {status}"
