from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Training, AttendanceRecord, AbsenceReason
from .forms import TrainingForm, AbsenceReasonForm


@login_required
def training_list_view(request):
    """Список всех тренировок и создание новой"""
    if request.method == 'POST':
        form = TrainingForm(request.POST, user=request.user)
        if form.is_valid():
            training = form.save(commit=False)
            training.created_by = request.user
            training.save()

            # Автоматически создаем записи посещаемости для всех игроков команды
            team_players = training.team.team_players.all()
            records = [
                AttendanceRecord(training=training, player=tp.player, is_present=True)
                for tp in team_players
            ]
            AttendanceRecord.objects.bulk_create(records)

            messages.success(request, 'Тренировка создана! Отметьте отсутствующих.')
            return redirect('attendance:detail', pk=training.pk)
    else:
        form = TrainingForm(user=request.user)

    trainings = Training.objects.filter(created_by=request.user).select_related('team')

    return render(request, 'attendance/training_list.html', {
        'trainings': trainings,
        'form': form,
    })


@login_required
def training_detail_view(request, pk):
    """Страница отметки посещаемости игрока на тренировке"""
    training = get_object_or_404(Training, pk=pk, created_by=request.user)

    if request.method == 'POST':
        # Сохранение статуса посещаемости игроков
        records = training.records.select_related('player')

        for record in records:
            # Чекбокс присутствия
            is_present = f'present_{record.id}' in request.POST
            reason_id = request.POST.get(f'reason_{record.id}')

            record.is_present = is_present
            if not is_present and reason_id:
                record.reason_id = reason_id
            else:
                record.reason = None

            record.save()

        messages.success(request, 'Данные о посещаемости успешно сохранены!')
        return redirect('attendance:detail', pk=training.pk)

    records = training.records.select_related('player', 'reason').order_by('player__name')

    # Причины пропусков: системные + созданные пользователем
    reasons = AbsenceReason.objects.filter(
        Q(is_default=True) | Q(created_by=request.user)
    )

    return render(request, 'attendance/training_detail.html', {
        'training': training,
        'records': records,
        'reasons': reasons,
    })


@login_required
def training_delete_view(request, pk):
    """Удаление тренировки"""
    training = get_object_or_404(Training, pk=pk, created_by=request.user)
    if request.method == 'POST':
        training.delete()
        messages.success(request, 'Запись о тренировке удалена.')
    return redirect('attendance:list')


@login_required
def reason_list_view(request):
    """Управление причинами пропусков (добавление новых)"""
    if request.method == 'POST':
        form = AbsenceReasonForm(request.POST)
        if form.is_valid():
            reason = form.save(commit=False)
            reason.created_by = request.user
            reason.is_default = False
            reason.save()
            messages.success(request, f'Причина "{reason.title}" добавлена!')
            return redirect('attendance:reasons')
    else:
        form = AbsenceReasonForm()

    reasons = AbsenceReason.objects.filter(
        Q(is_default=True) | Q(created_by=request.user)
    )

    return render(request, 'attendance/reason_list.html', {
        'reasons': reasons,
        'form': form,
    })
