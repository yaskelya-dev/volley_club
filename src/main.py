from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from src.api.v1 import (
    absence_reasons_router,
    attendance_router,
    players_router,
    teams_router,
    trainings_router,
    users_router,
)
from src.core.config import settings
from src.core.dependencies import (
    get_absence_reason_service,
    get_current_user,
    get_player_service,
    get_team_service,
    get_training_service,
)
from src.database.database import async_engine
from src.schemas.training import AttendanceItemRead, AttendanceUpsert
from src.schemas.user import UserRead
from src.services import NotFoundError, ValidationServiceError
from src.services.absence_reason_service import AbsenceReasonService
from src.services.player_service import PlayerService
from src.services.team_service import TeamService
from src.services.training_service import TrainingService


BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Жизненный цикл приложения без устаревшего @app.on_event."""
    yield
    await async_engine.dispose()


app = FastAPI(
    title="volleykarelia",
    description="Учёт игроков, команд, тренировок и посещаемости",
    debug=settings.DEBUG,
    lifespan=lifespan,
)


app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie=settings.SESSION_COOKIE_NAME,
    max_age=60 * 60 * 24 * 14,
    same_site="lax",
    https_only=False,
)


app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)

templates = Jinja2Templates(directory=BASE_DIR / "templates")


# Существующие API-роуты сохраняются.
# attendance_router только расширяет API новым POST /api/v1/attendance.
app.include_router(users_router, prefix="/api/v1")
app.include_router(players_router, prefix="/api/v1")
app.include_router(teams_router, prefix="/api/v1")
app.include_router(trainings_router, prefix="/api/v1")
app.include_router(attendance_router, prefix="/api/v1")
app.include_router(absence_reasons_router, prefix="/api/v1")


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
async def root(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse(
            url="/players",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return RedirectResponse(
        url="/login",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@app.get(
    "/login",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def login_page(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse(
            url="/players",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={},
    )


@app.get(
    "/register",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def register_page(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse(
            url="/players",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={},
    )


@app.post("/logout", include_in_schema=False)
async def logout(request: Request):
    request.session.clear()

    return RedirectResponse(
        url="/login",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@app.get(
    "/players",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def players_page(
    request: Request,
    current_user: UserRead = Depends(get_current_user),
    service: PlayerService = Depends(get_player_service),
):
    players = await service.list(current_user.id)

    return templates.TemplateResponse(
        request=request,
        name="players.html",
        context={
            "current_user": current_user,
            "players": players,
        },
    )


@app.post(
    "/players/{player_id}/delete",
    include_in_schema=False,
)
async def delete_player_page(
    player_id: int,
    current_user: UserRead = Depends(get_current_user),
    service: PlayerService = Depends(get_player_service),
):
    try:
        await service.delete(
            current_user.id,
            player_id,
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return RedirectResponse(
        url="/players",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@app.get(
    "/teams",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def teams_page(
    request: Request,
    current_user: UserRead = Depends(get_current_user),
    service: TeamService = Depends(get_team_service),
    player_service: PlayerService = Depends(get_player_service),
):
    teams = await service.list(current_user.id)
    players = await player_service.list(current_user.id)

    return templates.TemplateResponse(
        request=request,
        name="teams.html",
        context={
            "current_user": current_user,
            "teams": teams,
            "players": players,
        },
    )


@app.post(
    "/teams/{team_id}/delete",
    include_in_schema=False,
)
async def delete_team_page(
    team_id: int,
    current_user: UserRead = Depends(get_current_user),
    service: TeamService = Depends(get_team_service),
):
    try:
        # Используем тот же TeamService, что и API.
        await service.delete(
            current_user.id,
            team_id,
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return RedirectResponse(
        url="/teams",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@app.get(
    "/trainings",
    response_class=HTMLResponse,
    include_in_schema=False,
)
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
            (
                team
                for team in teams
                if team.id == candidate_id
            ),
            None,
        )

    # Без ?team_id показываем первую доступную команду.
    if selected_team is None and teams:
        selected_team = teams[0]

    attendance_view = None

    if selected_team is not None:
        attendance_view = (
            await training_service.get_attendance_view(
                current_user.id,
                selected_team.id,
            )
        )

    return templates.TemplateResponse(
        request=request,
        name="trainings.html",
        context={
            "current_user": current_user,
            "teams": teams,
            "selected_team": selected_team,
            "attendance_view": attendance_view,
        },
    )


@app.get(
    "/trainings/{team_id}/all",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def all_trainings_page(
    request: Request,
    team_id: int,
    current_user: UserRead = Depends(get_current_user),
    team_service: TeamService = Depends(get_team_service),
    training_service: TrainingService = Depends(get_training_service),
):
    try:
        team = await team_service.get(
            current_user.id,
            team_id,
        )

        attendance_view = (
            await training_service.get_all_attendance_view(
                current_user.id,
                team_id,
            )
        )

    except NotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return templates.TemplateResponse(
        request=request,
        name="trainings_all.html",
        context={
            "current_user": current_user,
            "team": team,
            "attendance_view": attendance_view,
        },
    )


@app.post(
    "/trainings/attendance",
    response_model=AttendanceItemRead,
    include_in_schema=False,
)
async def web_upsert_attendance(
    payload: AttendanceUpsert,
    current_user: UserRead = Depends(get_current_user),
    service: TrainingService = Depends(get_training_service),
) -> AttendanceItemRead:
    """Web JSON-route. Использует тот же сервис, что и API."""
    try:
        return await service.upsert_attendance(
            current_user.id,
            payload,
        )

    except NotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except ValidationServiceError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc


@app.post(
    "/trainings/{training_id}/delete",
    include_in_schema=False,
)
async def delete_training_page(
    training_id: int,
    request: Request,
    current_user: UserRead = Depends(get_current_user),
    training_service: TrainingService = Depends(get_training_service),
):
    try:
        training = await training_service.get(
            current_user.id,
            training_id,
        )

        team_id = training.team_id

        await training_service.delete(
            current_user.id,
            training_id,
        )

    except NotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    raw_return_team_id = request.query_params.get(
        "team_id"
    )

    return_team_id = (
        int(raw_return_team_id)
        if raw_return_team_id
        and raw_return_team_id.isdigit()
        else team_id
    )

    return RedirectResponse(
        url=f"/trainings?team_id={return_team_id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@app.get(
    "/trainings/{team_id}",
    include_in_schema=False,
)
async def legacy_training_team_page(team_id: int):
    """Старый URL сохраняем для совместимости."""
    return RedirectResponse(
        url=f"/trainings?team_id={team_id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@app.get(
    "/absence-reasons",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def absence_reasons_page(
    request: Request,
    current_user: UserRead = Depends(get_current_user),
    service: AbsenceReasonService = Depends(
        get_absence_reason_service
    ),
):
    reasons = await service.list(
        current_user.id
    )

    return templates.TemplateResponse(
        request=request,
        name="absence_reasons.html",
        context={
            "current_user": current_user,
            "reasons": reasons,
        },
    )


@app.post(
    "/absence-reasons/{reason_id}/delete",
    include_in_schema=False,
)
async def delete_absence_reason_page(
    reason_id: int,
    current_user: UserRead = Depends(get_current_user),
    service: AbsenceReasonService = Depends(
        get_absence_reason_service
    ),
):
    try:
        await service.delete(
            current_user.id,
            reason_id,
        )

    except NotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return RedirectResponse(
        url="/absence-reasons",
        status_code=status.HTTP_303_SEE_OTHER,
    )


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
