import re
from datetime import datetime
import requests
from django.db import transaction
from .models import TrackedTeam, Game

TEAMS_JSON_URL = 'https://volleypgo.ru/s-26-27/teams.json'
SCHEDULE_JSON_URL = 'https://volleypgo.ru/s-26-27/schedule.json'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

MONTHS_RU = {
    'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
    'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
    'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
}


def _parse_game_date(raw_date_str: str):
    """Преобразует строку с датой в объект datetime.date."""
    if not raw_date_str:
        return None

    raw_date_str = raw_date_str.strip()

    # 1. Попытка распарсить формат YYYY-MM-DD
    try:
        return datetime.strptime(raw_date_str, "%Y-%m-%d").date()
    except ValueError:
        pass

    # 2. Попытка распарсить формат DD.MM.YYYY
    try:
        return datetime.strptime(raw_date_str, "%d.%m.%Y").date()
    except ValueError:
        pass

    # 3. Попытка распарсить русский формат (например: "4 октября 2026 г.")
    match = re.search(r'(\d{1,2})\s+([а-яА-Я]+)\s+(\d{4})', raw_date_str)
    if match:
        day, month_str, year = match.groups()
        month_num = MONTHS_RU.get(month_str.lower())
        if month_num:
            try:
                return datetime(int(year), month_num, int(day)).date()
            except ValueError:
                pass

    return None


def _fetch_json(url: str) -> dict:
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()
    return response.json()


def _extract_team_info(input_str: str, teams_list: list) -> dict:
    clean_input = input_str.strip().lower()

    for team in teams_list:
        if team.get("id", "").lower() == clean_input:
            return team

    for team in teams_list:
        team_id = team.get("id", "").lower()
        if team_id and team_id in clean_input:
            return team

    for team in teams_list:
        if team.get("name", "").lower() == clean_input:
            return team

    raise ValueError(f"Команда по запросу '{input_str}' не найдена в базе данных сайта.")


def update_team_data_from_json(url_or_id: str, user=None) -> TrackedTeam:
    teams_data = _fetch_json(TEAMS_JSON_URL)
    schedule_data = _fetch_json(SCHEDULE_JSON_URL)

    leagues_map = {
        league["id"]: league["name"]
        for league in teams_data.get("leagues", [])
    }

    target_team = _extract_team_info(url_or_id, teams_data.get("teams", []))
    team_id_slug = target_team["id"]
    team_name = target_team["name"]
    league_name = leagues_map.get(target_team.get("leagueId"), "")

    with transaction.atomic():
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

        team_obj.games.all().delete()

        games_to_create = []
        for g in schedule_data.get("games", []):
            if g.get("team1Id") == team_id_slug or g.get("team2Id") == team_id_slug:

                matchup_text = f"{g['team1']} — {g['team2']}"
                raw_date = g.get('date', '')
                date_str = f"{raw_date} {g.get('time', '')}".strip()
                parsed_date = _parse_game_date(raw_date)

                score_str = ""
                if g.get("score1") is not None and g.get("score2") is not None:
                    score_str = f"{g['score1']}:{g['score2']}"

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
                        game_date=parsed_date,
                        score=score_str
                    )
                )

        Game.objects.bulk_create(games_to_create)

    return team_obj
