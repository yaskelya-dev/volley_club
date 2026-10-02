from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from users.decorators import login_required_message
from .models import Team, TeamPlayer
from .forms import TeamForm, TeamPlayerAddForm


@login_required_message()
def team_list_view(request):
    """Список всех команд пользователя + создание новой с редиректом на добавление игроков."""
    if request.method == 'POST':
        form = TeamForm(request.POST)
        if form.is_valid():
            team = form.save(commit=False)
            team.owner = request.user
            team.save()
            messages.success(request, f'Команда "{team.title}" создана! Теперь добавьте игроков в состав.')
            # Сразу перенаправляем на страницу редактирования/добавления игроков
            return redirect('teams:detail', pk=team.pk)
    else:
        form = TeamForm()

    teams = Team.objects.filter(owner=request.user).order_by('title')

    return render(request, 'teams/teams_list.html', {
        'teams': teams,
        'form': form,
    })


@login_required_message()
def team_detail_view(request, pk):
    """Страница редактирования названия команды и управления составом."""
    team = get_object_or_404(Team, pk=pk, owner=request.user)

    if request.method == 'POST':
        team_form = TeamForm(request.POST, instance=team)
        if team_form.is_valid():
            team_form.save()
            messages.success(request, 'Название команды обновлено.')
            return redirect('teams:detail', pk=team.pk)
    else:
        team_form = TeamForm(instance=team)

    # Получаем состав команды, отсортированный по игровому номеру
    team_players = team.team_players.select_related('player').order_by('number')
    add_player_form = TeamPlayerAddForm(user=request.user, team=team)

    return render(request, 'teams/team_detail.html', {
        'team': team,
        'team_form': team_form,
        'team_players': team_players,
        'add_player_form': add_player_form,
    })


@login_required_message()
def add_player_view(request, pk):
    """Добавление игрока в состав команды."""
    team = get_object_or_404(Team, pk=pk, owner=request.user)

    if request.method == 'POST':
        form = TeamPlayerAddForm(request.POST, user=request.user, team=team)
        if form.is_valid():
            team_player = form.save(commit=False)
            team_player.team = team

            # Проверка уникальности номера в команде
            if TeamPlayer.objects.filter(team=team, number=team_player.number).exists():
                messages.error(request, f'Игровой номер #{team_player.number} уже занят в этой команде!')
            else:
                team_player.save()
                messages.success(request, f'Игрок {team_player.player.name} добавлен под номером #{team_player.number}.')
        else:
            messages.error(request, 'Ошибка при добавлении игрока. Проверьте введенные данные.')

    return redirect('teams:detail', pk=pk)


@login_required_message()
def remove_player_view(request, pk, player_pk):
    """Удаление игрока из состава команды."""
    team = get_object_or_404(Team, pk=pk, owner=request.user)
    team_player = get_object_or_404(TeamPlayer, team=team, player_id=player_pk)

    if request.method == 'POST':
        player_name = team_player.player.name
        team_player.delete()
        messages.success(request, f'Игрок "{player_name}" удален из состава команды.')

    return redirect('teams:detail', pk=pk)


@login_required_message()
def team_delete_view(request, pk):
    """Удаление всей команды."""
    team = get_object_or_404(Team, pk=pk, owner=request.user)

    if request.method == 'POST':
        team_title = team.title
        team.delete()
        messages.success(request, f'Команда "{team_title}" удалена.')

    return redirect('teams:list')
