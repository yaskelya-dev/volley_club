from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from users.decorators import login_required_message
from .models import Player
from .forms import PlayerForm


@login_required_message()
def player_list_view(request):
    if request.method == 'POST':
        form = PlayerForm(request.POST)
        if form.is_valid():
            player = form.save(commit=False)
            player.created_by = request.user
            player.save()
            messages.success(request, f'Игрок "{player.name}" успешно добавлен!')
            return redirect('players:list')
    else:
        form = PlayerForm()

    # Сортировка по алфавиту (order_by('name'))
    players = Player.objects.filter(created_by=request.user).order_by('name')

    return render(request, 'players/players_list.html', {
        'players': players,
        'form': form,
    })


@login_required_message()
def player_detail_view(request, pk):
    player = get_object_or_404(Player, pk=pk, created_by=request.user)

    if request.method == 'POST':
        form = PlayerForm(request.POST, instance=player)
        if form.is_valid():
            form.save()
            messages.success(request, f'Данные игрока "{player.name}" успешно обновлены.')
            return redirect('players:list')
    else:
        form = PlayerForm(instance=player)

    return render(request, 'players/player_detail.html', {
        'player': player,
        'form': form,
    })


@login_required_message()
def player_delete_view(request, pk):
    player = get_object_or_404(Player, pk=pk, created_by=request.user)

    if request.method == 'POST':
        player_name = player.name
        player.delete()
        messages.success(request, f'Игрок "{player_name}" был удален.')

    return redirect('players:list')
