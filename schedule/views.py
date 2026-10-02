from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from users.decorators import login_required_message
from .models import TrackedTeam, Game
from .forms import AddTrackedTeamForm, GameFilterForm
from .services import update_team_data_from_json


@login_required_message()
def schedule_index(request):
    form = AddTrackedTeamForm()

    if request.method == 'POST':
        form = AddTrackedTeamForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']
            try:
                team = update_team_data_from_json(url, user=request.user)
                messages.success(request, f'Команда "{team.name}" успешно добавлена в отслеживаемые!')
                return redirect('schedule:index')
            except Exception as e:
                messages.error(request, f'Ошибка при получении данных: {e}')

    # 1. Получаем команды текущего пользователя
    user_teams = request.user.tracked_teams.prefetch_related('games').all()

    # 2. Инициализируем форму фильтрации из GET-параметров
    filter_form = GameFilterForm(request.GET, user=request.user)

    # 3. Базовые QuerySet'ы для игр
    upcoming_games = Game.objects.filter(
        team__in=user_teams,
        status=Game.GameStatus.UPCOMING
    ).select_related('team').order_by('game_date')

    completed_games = Game.objects.filter(
        team__in=user_teams,
        status=Game.GameStatus.COMPLETED
    ).select_related('team').order_by(
        '-game_date')

    # 4. Применяем фильтры, если форма валидна
    if filter_form.is_valid():
        selected_team = filter_form.cleaned_data.get('team')
        date_from = filter_form.cleaned_data.get('date_from')
        date_to = filter_form.cleaned_data.get('date_to')

        if selected_team:
            upcoming_games = upcoming_games.filter(team=selected_team)
            completed_games = completed_games.filter(team=selected_team)

        if date_from:
            upcoming_games = upcoming_games.filter(game_date__gte=date_from)
            completed_games = completed_games.filter(game_date__gte=date_from)

        if date_to:
            upcoming_games = upcoming_games.filter(game_date__lte=date_to)
            completed_games = completed_games.filter(game_date__lte=date_to)

    context = {
        'form': form,
        'filter_form': filter_form,
        'user_teams': user_teams,
        'upcoming_games': upcoming_games,
        'completed_games': completed_games,
    }
    return render(request, 'schedule/index.html', context)


@login_required_message()
def refresh_team(request, team_id):
    team = get_object_or_404(TrackedTeam, id=team_id)
    try:
        update_team_data_from_json(team.url, user=request.user)
        messages.success(request, f'Расписание команды "{team.name}" обновлено!')
    except Exception as e:
        messages.error(request, f'Не удалось обновить расписание: {e}')
    return redirect('schedule:index')


@login_required_message()
def remove_team_from_user(request, team_id):
    team = get_object_or_404(TrackedTeam, id=team_id)
    team.users.remove(request.user)
    messages.info(request, f'Команда "{team.name}" удалена из вашего списка.')
    return redirect('schedule:index')
