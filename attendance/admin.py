from django.contrib import admin
from .models import AbsenceReason, Training, AttendanceRecord


class AttendanceRecordInline(admin.TabularInline):
    model = AttendanceRecord
    extra = 0


@admin.register(Training)
class TrainingAdmin(admin.ModelAdmin):
    list_display = ('team', 'date', 'created_by', 'created_at')
    list_filter = ('team', 'date')
    inlines = [AttendanceRecordInline]


@admin.register(AbsenceReason)
class AbsenceReasonAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_default', 'created_by')
    list_filter = ('is_default',)
