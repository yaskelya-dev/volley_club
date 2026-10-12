from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from src.core.dependencies import (
    get_absence_reason_service,
    get_current_user,
    get_player_service,
    get_team_service,
    get_training_service,
)
from src.schemas.training import AttendanceItemRead, AttendanceUpsert
from src.schemas.user import UserRead
from src.services import NotFoundError, ValidationServiceError
from src.services.absence_reason_service import AbsenceReasonService
from src.services.player_service import PlayerService
from src.services.team_service import TeamService
from src.services.training_service import TrainingService

router = APIRouter(include_in_schema=False)


def _safe_next_url(value: str | None) -> str:
    """Accept only a relative in-app URL for post-login navigation."""
    if not value or not value.startswith("/") or value.startswith("//"):
        return "/players"
    if "\\" in value:
        return "/players"

    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc:
        return "/players"
    return value


def _render(request: Request, template_name: str, **context):
    """Use the Jinja environment configured once by src.main."""
    page_context = {
        "asset_version": request.app.state.asset_version,
        **context,
    }
    return request.app.state.templates.TemplateResponse(
        request=request,
        name=template_name,
        context=page_context,
    )


@router.get("/", include_in_schema=False)
async def root(request: Request):
    destination = "/players" if request.session.get("user_id") else "/login"
    return RedirectResponse(url=destination, status_code=303)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse(url="/players", status_code=303)

    return _render(
        request,
        "login.html",
        next_url=_safe_next_url(request.query_params.get("next")),
    )


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse(url="/players", status_code=303)
    return _render(request, "register.html")


@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)


@router.get("/players", response_class=HTMLResponse)
async def players_page(
    request: Request,
    current_user: UserRead = Depends(get_current_user),
    service: PlayerService = Depends(get_player_service),
):
    players = await service.list(current_user.id)
    return _render(
        request,
        "players.html",
        current_user=current_user,
        players=players,
    )


@router.get("/teams", response_class=HTMLResponse)
async def teams_page(
    request: Request,
    current_user: UserRead = Depends(get_current_user),
    service: TeamService = Depends(get_team_service),
    player_service: PlayerService = Depends(get_player_service),
):
    teams = await service.list(current_user.id)
    players = await player_service.list(current_user.id)

    # A player can belong to multiple teams, but should not be offered again
    # for a team where the player is already a member.
    available_players_by_team = {
        team.id: [
            player
            for player in players
            if player.id not in {member.id for member in team.players}
        ]
        for team in teams
    }

    return _render(
        request,
        "teams.html",
        current_user=current_user,
        teams=teams,
        players=players,
        available_players_by_team=available_players_by_team,
    )


@router.get("/trainings", response_class=HTMLResponse)
async def trainings_page(
    request: Request,
    current_user: UserRead = Depends(get_current_user),
    team_service: TeamService = Depends(get_team_service),
    training_service: TrainingService = Depends(get_training_service),
):
    teams = await team_service.list(current_user.id)
    selected_team = None
    raw_team_id = request.query_params.get("team_id")

    if raw_team_id and raw_team_id.isdigit():
        candidate_id = int(raw_team_id)
        selected_team = next(
            (team for team in teams if team.id == candidate_id),
            None,
        )

    if selected_team is None and teams:
        selected_team = teams[0]

    attendance_view = None
    if selected_team is not None:
        attendance_view = await training_service.get_attendance_view(
            current_user.id,
            selected_team.id,
        )

    return _render(
        request,
        "trainings.html",
        current_user=current_user,
        teams=teams,
        selected_team=selected_team,
        attendance_view=attendance_view,
    )


@router.get("/trainings/{team_id}/all", response_class=HTMLResponse)
async def all_trainings_page(
    request: Request,
    team_id: int,
    current_user: UserRead = Depends(get_current_user),
    team_service: TeamService = Depends(get_team_service),
    training_service: TrainingService = Depends(get_training_service),
):
    try:
        team = await team_service.get(current_user.id, team_id)
        attendance_view = await training_service.get_all_attendance_view(
            current_user.id,
            team_id,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return _render(
        request,
        "trainings_all.html",
        current_user=current_user,
        team=team,
        attendance_view=attendance_view,
    )


@router.post(
    "/trainings/attendance",
    response_model=AttendanceItemRead,
)
async def web_upsert_attendance(
    payload: AttendanceUpsert,
    current_user: UserRead = Depends(get_current_user),
    service: TrainingService = Depends(get_training_service),
) -> AttendanceItemRead:
    try:
        return await service.upsert_attendance(current_user.id, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationServiceError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/absence-reasons", response_class=HTMLResponse)
async def absence_reasons_page(
    request: Request,
    current_user: UserRead = Depends(get_current_user),
    service: AbsenceReasonService = Depends(get_absence_reason_service),
):
    reasons = await service.list(current_user.id)
    return _render(
        request,
        "absence_reasons.html",
        current_user=current_user,
        reasons=reasons,
    )
