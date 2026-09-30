import requests
from bs4 import BeautifulSoup
from .models import TrackedTeam, Game


def parse_and_update_team(url: str, user=None) -> TrackedTeam:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, 'html.parser')

    # 1. Извлечение названия команды и лиги
    main_elem = soup.find('main', id='team-page')
    team_name = main_elem.get('data-team-name') if main_elem else None

    if not team_name:
        h1 = soup.find('h1')
        team_name = h1.text.strip() if h1 else 'Неизвестная команда'

    league_name = main_elem.get('data-league-name') if main_elem else ''
    if not league_name:
        meta_div = soup.find('div', class_='meta')
        if meta_div:
            league_name = meta_div.text.strip().split('·')[0].strip()

    # 2. Создаем или получаем отслеживаемую команду (get_or_create)
    team, created = TrackedTeam.objects.get_or_create(
        url=url,
        defaults={
            'name': team_name,
            'league': league_name,
        }
    )

    # Обновляем мета-данные
    team.name = team_name
    team.league = league_name

    if user and user.is_authenticated:
        team.users.add(user)
    team.save()

    # 3. Обновление расписания игр
    # Для простоты очистим предыдущие сохраненные игры команды и перезапишем актуальными
    team.games.all().delete()

    # --- Предстоящие игры ---
    upcoming_div = soup.find('div', id='upcoming-games')
    if upcoming_div:
        for article in upcoming_div.find_all('article', class_='game'):
            teams_div = article.find('div', class_='game-teams')
            date_div = article.find('div', class_='game-date')

            matchup = teams_div.text.strip() if teams_div else ''
            game_date = date_div.text.strip() if date_div else ''

            if matchup and game_date:
                Game.objects.create(
                    team=team,
                    status=Game.GameStatus.UPCOMING,
                    matchup_text=matchup,
                    date_str=game_date
                )

    # --- Завершённые игры ---
    completed_div = soup.find('div', id='completed-games')
    if completed_div:
        for article in completed_div.find_all('article', class_='completed-game'):
            date_div = article.find('div', class_='completed-game-date')
            matchup_div = article.find('div', class_='completed-game-matchup')
            score_div = article.find('div', class_='completed-game-score')

            game_date = date_div.text.strip() if date_div else ''
            score = score_div.text.strip() if score_div else ''

            # Извлекаем названия команд из блоков home и away
            home_team = matchup_div.find('div', class_='completed-game-team home') if matchup_div else None
            away_team = matchup_div.find('div', class_='completed-game-team away') if matchup_div else None

            home_name = home_team.text.strip() if home_team else ''
            away_name = away_team.text.strip() if away_team else ''

            matchup = f"{home_name} — {away_name}".strip(" —")

            if matchup and game_date:
                Game.objects.create(
                    team=team,
                    status=Game.GameStatus.COMPLETED,
                    matchup_text=matchup,
                    date_str=game_date,
                    score=score
                )

    return team
