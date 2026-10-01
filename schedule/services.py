import requests
from django.db import transaction
from .models import TrackedTeam, Game

# Замените на прямые ссылки на JSON-файлы с вашего сервера/сайта
TEAMS_JSON_URL = 'https://volleypgo.ru/s-26-27/teams.json'
SCHEDULE_JSON_URL = 'https://volleypgo.ru/s-26-27/schedule.json'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}


def _fetch_json(url: str) -> dict:
    """Вспомогательная функция для загрузки JSON по URL."""
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()
    return response.json()


def _extract_team_info(input_str: str, teams_list: list) -> dict:
    """
    Ищет команду в списке по ID, названию или совпадению фрагмента URL.
    """
    clean_input = input_str.strip().lower()

    # 1. Точное совпадение по ID команды
    for team in teams_list:
        if team.get("id", "").lower() == clean_input:
            return team

    # 2. Поиск ID внутри переданного URL (например: https://site.com/teams/mfcn)
    for team in teams_list:
        team_id = team.get("id", "").lower()
        if team_id and team_id in clean_input:
            return team

    # 3. Совпадение по названию команды
    for team in teams_list:
        if team.get("name", "").lower() == clean_input:
            return team

    raise ValueError(f"Команда по запросу '{input_str}' не найдена в базе данных сайта.")


def update_team_data_from_json(url_or_id: str, user=None) -> TrackedTeam:
    teams_data = _fetch_json(TEAMS_JSON_URL)
    schedule_data = _fetch_json(SCHEDULE_JSON_URL)

    # Карта названий лиг: {"men-1": "1 мужская лига", ...}
    leagues_map = {
        league["id"]: league["name"]
        for league in teams_data.get("leagues", [])
    }

    # Поиск команды в полученном JSON
    target_team = _extract_team_info(url_or_id, teams_data.get("teams", []))
    team_id_slug = target_team["id"]
    team_name = target_team["name"]
    league_name = leagues_map.get(target_team.get("leagueId"), "")

    with transaction.atomic():
        # Создание или обновление отслеживаемой команды
        team_obj, _ = TrackedTeam.objects.get_or_create(
            url=url_or_id,
            defaults={
                'name': team_name,
                'league': league_name,
            }
        )

        team_obj.name = team_name
        team_obj.league = league_name

        if user and user.is_authenticated:
            team_obj.users.add(user)

        team_obj.save()

        # Полная актуализация списка игр
        team_obj.games.all().delete()

        games_to_create = []
        for g in schedule_data.get("games", []):
            # Проверка участия команды в игре
            if g.get("team1Id") == team_id_slug or g.get("team2Id") == team_id_slug:

                matchup_text = f"{g['team1']} — {g['team2']}"
                date_str = f"{g.get('date', '')} {g.get('time', '')}".strip()

                # Счёт формируется при его наличии
                score_str = ""
                if g.get("score1") is not None and g.get("score2") is not None:
                    score_str = f"{g['score1']}:{g['score2']}"

                # Маппинг статусов
                raw_status = g.get("status", "")
                if raw_status == "Завершён":
                    status = Game.GameStatus.COMPLETED
                else:
                    status = Game.GameStatus.UPCOMING

                games_to_create.append(
                    Game(
                        team=team_obj,
                        status=status,
                        matchup_text=matchup_text,
                        date_str=date_str,
                        score=score_str
                    )
                )

        Game.objects.bulk_create(games_to_create)

    return team_obj
