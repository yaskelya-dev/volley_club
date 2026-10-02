from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from users.decorators import login_required_message
from .models import Training, AttendanceRecord, AbsenceReason
from .forms import TrainingForm, AbsenceReasonForm
from teams.models import Team


@login_required_message()
def attendance_matrix_view(request):
    """Единый рабочий стол посещаемости с матричной таблицей."""
    user_teams = Team.objects.filter(owner=request.user).order_by('title')

    if not user_teams.exists():
        return render(request, 'attendance/matrix.html', {'teams': []})

    # Определяем текущую выбранную команду
    selected_team_id = request.GET.get('team') or request.POST.get('team_id')
    if selected_team_id:
        current_team = get_object_or_404(Team, id=selected_team_id, owner=request.user)
    else:
        current_team = user_teams.first()

    # --- ОБРАБОТКА POST-ЗАПРОСОВ ---
    if request.method == 'POST':
        action = request.POST.get('action')

        # 1. Добавление новой тренировки
        if action == 'add_training':
            training_form = TrainingForm(request.POST, user=request.user)
            if training_form.is_valid():
                training = training_form.save(commit=False)
                training.created_by = request.user
                training.save()

                # Автосоздание записей "Был" для всех игроков команды
                team_players = training.team.team_players.all()
                records = [
                    AttendanceRecord(training=training, player=tp.player, is_present=True)
                    for tp in team_players
                ]
                AttendanceRecord.objects.bulk_create(records)

                messages.success(request, f'Тренировка на {training.date.strftime("%d.%m.%Y")} добавлена!')
                return redirect(f"{request.path}?team={training.team.id}")

        # 2. Быстрое добавление новой причины пропуска
        elif action == 'add_reason':
            reason_form = AbsenceReasonForm(request.POST)
            if reason_form.is_valid():
                reason = reason_form.save(commit=False)
                reason.created_by = request.user
                reason.is_default = False
                reason.save()
                messages.success(request, f'Причина "{reason.title}" успешно добавлена!')
                return redirect(f"{request.path}?team={current_team.id}")

        # 3. Сохранение посещаемости для конкретной тренировки (из модального окна)
        elif action == 'update_attendance':
            training_id = request.POST.get('training_id')
            training = get_object_or_404(Training, id=training_id, created_by=request.user)
            records = training.records.select_related('player')

            for record in records:
                is_present = f'present_{record.id}' in request.POST
                reason_id = request.POST.get(f'reason_{record.id}')

                record.is_present = is_present
                if not is_present and reason_id:
                    record.reason_id = reason_id
                else:
                    record.reason = None
                record.save()

            messages.success(request, f'Посещаемость за {training.date.strftime("%d.%m.%Y")} обновлена.')
            return redirect(f"{request.path}?team={current_team.id}")

    # --- ФОРМИРОВАНИЕ СТРУКТУРЫ МАТРИЦЫ ---
    # Список игроков выбранной команды (упорядочен по номеру)
    team_players = current_team.team_players.select_related('player').order_by('player__name')
    players = [tp.player for tp in team_players]

    # Все тренировки выбранной команды по возрастанию даты
    trainings = Training.objects.filter(team=current_team).order_by('date')

    # Загружаем все записи посещаемости и создаем карту (training_id, player_id) -> record
    records = AttendanceRecord.objects.filter(
        training__in=trainings
    ).select_related('reason')

    attendance_map = {(r.training_id, r.player_id): r for r in records}

    # Сборка строк таблицы-матрицы для ВСЕХ тренировок
    all_matrix_rows = []
    for idx, training in enumerate(trainings, start=1):
        player_statuses = []
        for player in players:
            rec = attendance_map.get((training.id, player.id))
            player_statuses.append({
                'player_id': player.id,
                'record': rec,
                'is_present': rec.is_present if rec else True,
                'reason': rec.reason if rec else None
            })

        all_matrix_rows.append({
            'number': idx,
            'training': training,
            'player_statuses': player_statuses
        })

    # --- ФИЛЬТРАЦИЯ ДЛЯ ТЕКУЩЕГО ОТОБРАЖЕНИЯ (1 предыдущая и 2 следующие) ---
    today = timezone.now().date()

    # Разделяем тренировки на прошедшие и предстоящие (включая сегодня)
    past_rows = [row for row in all_matrix_rows if row['training'].date < today]
    future_rows = [row for row in all_matrix_rows if row['training'].date >= today]

    # Берем 1 последнюю прошедшую и 2 ближайшие будущие тренировки
    recent_matrix_rows = past_rows[-1:] + future_rows[:2]

    # Причины пропусков для выбора в модальном окне
    reasons = AbsenceReason.objects.filter(
        Q(is_default=True) | Q(created_by=request.user)
    )

    training_form = TrainingForm(user=request.user, initial={'team': current_team})
    reason_form = AbsenceReasonForm()

    return render(request, 'attendance/matrix.html', {
        'teams': user_teams,
        'current_team': current_team,
        'players': players,
        'recent_matrix_rows': recent_matrix_rows,  # За 3 недели (для таблицы)
        'all_matrix_rows': all_matrix_rows,        # Все тренировки (для модального окна)
        'reasons': reasons,
        'training_form': training_form,
        'reason_form': reason_form,
    })


@login_required_message()
def training_delete_view(request, pk):
    """Удаление тренировки."""
    training = get_object_or_404(Training, pk=pk, created_by=request.user)
    team_id = training.team.id
    if request.method == 'POST':
        training.delete()
        messages.success(request, 'Тренировка удалена.')
    return redirect(f"{reverse('attendance:list')}?team={team_id}")


@login_required_message()
def reason_edit_view(request, pk):
    """Редактирование пользовательской причины пропуска."""
    reason = get_object_or_404(AbsenceReason, pk=pk, created_by=request.user, is_default=False)
    team_id = request.GET.get('team') or request.POST.get('team_id')

    if request.method == 'POST':
        form = AbsenceReasonForm(request.POST, instance=reason)
        if form.is_valid():
            form.save()
            messages.success(request, f'Причина "{reason.title}" успешно обновлена.')
        else:
            messages.error(request, 'Ошибка при редактировании причины.')

    redirect_url = reverse('attendance:list')
    if team_id:
        redirect_url += f'?team={team_id}'
    return redirect(redirect_url)


@login_required_message()
def reason_delete_view(request, pk):
    """Удаление пользовательской причины пропуска."""
    reason = get_object_or_404(AbsenceReason, pk=pk, created_by=request.user, is_default=False)
    team_id = request.GET.get('team') or request.POST.get('team_id')

    if request.method == 'POST':
        title = reason.title
        # Так как в AttendanceRecord у поля reason стоит on_delete=models.SET_NULL,
        # у связанных записей поле причиной станет None (Н/Я)
        reason.delete()
        messages.success(request, f'Причина "{title}" удалена.')

    redirect_url = reverse('attendance:list')
    if team_id:
        redirect_url += f'?team={team_id}'
    return redirect(redirect_url)
