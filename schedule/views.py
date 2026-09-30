from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import TrackedTeam, Game
from .forms import AddTrackedTeamForm
from .services import parse_and_update_team


@login_required
def schedule_index(request):
    form = AddTrackedTeamForm()

    if request.method == 'POST':
        form = AddTrackedTeamForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']
            try:
                team = parse_and_update_team(url, user=request.user)
                messages.success(request, f'Команда "{team.name}" успешно добавлена в отслеживаемые!')
                return redirect('schedule:index')
            except Exception as e:
                messages.error(request, f'Ошибка при получении данных с сайта: {e}')

    # Получаем команды, отслеживаемые текущим пользователем
    user_teams = request.user.tracked_teams.prefetch_related('games').all()

    # Все предстоящие и завершенные игры для отслеживаемых команд
    upcoming_games = Game.objects.filter(
        team__in=user_teams,
        status=Game.GameStatus.UPCOMING
    ).select_related('team')

    completed_games = Game.objects.filter(
        team__in=user_teams,
        status=Game.GameStatus.COMPLETED
    ).select_related('team')

    context = {
        'form': form,
        'user_teams': user_teams,
        'upcoming_games': upcoming_games,
        'completed_games': completed_games,
    }
    return render(request, 'schedule/index.html', context)


@login_required
def refresh_team(request, team_id):
    """Обновление расписания конкретной команды"""
    team = get_object_or_404(TrackedTeam, id=team_id)
    try:
        parse_and_update_team(team.url, user=request.user)
        messages.success(request, f'Расписание команды "{team.name}" обновлено!')
    except Exception as e:
        messages.error(request, f'Не удалось обновить расписание: {e}')
    return redirect('schedule:index')


@login_required
def remove_team_from_user(request, team_id):
    """Удаление команды из списка отслеживаемых пользователем"""
    team = get_object_or_404(TrackedTeam, id=team_id)
    team.users.remove(request.user)
    messages.info(request, f'Команда "{team.name}" удалена из вашего списка.')
    return redirect('schedule:index')
