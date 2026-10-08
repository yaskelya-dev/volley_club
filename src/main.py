from contextlib import asynccontextmanager
import hashlib
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

from src.schemas.training import (
    AttendanceItemRead,
    AttendanceUpsert,
)

from src.schemas.user import UserRead

from src.services import (
    NotFoundError,
    ValidationServiceError,
)

from src.services.absence_reason_service import (
    AbsenceReasonService,
)

from src.services.player_service import (
    PlayerService,
)

from src.services.team_service import (
    TeamService,
)

from src.services.training_service import (
    TrainingService,
)


BASE_DIR = Path(__file__).resolve().parent

STATIC_DIR = BASE_DIR / "static"

STATIC_CSS = (
    STATIC_DIR
    / "css"
    / "style.css"
)


if not STATIC_CSS.is_file():
    raise RuntimeError(
        f"Static CSS is missing: {STATIC_CSS}"
    )


# Версия CSS меняется автоматически при изменении файла.
ASSET_VERSION = (
    hashlib
    .sha256(
        STATIC_CSS.read_bytes()
    )
    .hexdigest()[:12]
)


@asynccontextmanager
async def lifespan(
    _: FastAPI,
) -> AsyncIterator[None]:

    yield

    await async_engine.dispose()


app = FastAPI(
    title="volleykarelia",

    description=(
        "Учёт игроков, команд, "
        "тренировок и посещаемости"
    ),

    debug=settings.DEBUG,

    lifespan=lifespan,
)


app.add_middleware(
    SessionMiddleware,

    secret_key=settings.SECRET_KEY,

    session_cookie=(
        settings.SESSION_COOKIE_NAME
    ),

    max_age=60 * 60 * 24 * 14,

    same_site="lax",

    https_only=False,
)


# Статика монтируется абсолютным путём.
# Важно: до подключения остальных маршрутов.
app.mount(
    "/static",

    StaticFiles(
        directory=STATIC_DIR
    ),

    name="static",
)


templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)


app.include_router(
    users_router,
    prefix="/api/v1",
)

app.include_router(
    players_router,
    prefix="/api/v1",
)

app.include_router(
    teams_router,
    prefix="/api/v1",
)

app.include_router(
    trainings_router,
    prefix="/api/v1",
)

app.include_router(
    attendance_router,
    prefix="/api/v1",
)

app.include_router(
    absence_reasons_router,
    prefix="/api/v1",
)


@app.get(
    "/health",
    tags=["system"],
)
async def health():
    return {
        "status": "ok"
    }


@app.get(
    "/",
    include_in_schema=False,
)
async def root(
    request: Request,
):

    if request.session.get(
        "user_id"
    ):

        return RedirectResponse(
            url="/players",
            status_code=303,
        )


    return RedirectResponse(
        url="/login",
        status_code=303,
    )


@app.get(
    "/login",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def login_page(
    request: Request,
):

    if request.session.get(
        "user_id"
    ):

        return RedirectResponse(
            url="/players",
            status_code=303,
        )


    return templates.TemplateResponse(
        request=request,

        name="login.html",

        context={
            "asset_version":
                ASSET_VERSION,
        },
    )


@app.get(
    "/register",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def register_page(
    request: Request,
):

    if request.session.get(
        "user_id"
    ):

        return RedirectResponse(
            url="/players",
            status_code=303,
        )


    return templates.TemplateResponse(
        request=request,

        name="register.html",

        context={
            "asset_version":
                ASSET_VERSION,
        },
    )


@app.post(
    "/logout",
    include_in_schema=False,
)
async def logout(
    request: Request,
):

    request.session.clear()


    return RedirectResponse(
        url="/login",
        status_code=303,
    )


@app.get(
    "/players",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def players_page(
    request: Request,

    current_user: UserRead = Depends(
        get_current_user
    ),

    service: PlayerService = Depends(
        get_player_service
    ),
):

    players = await service.list(
        current_user.id
    )


    return templates.TemplateResponse(
        request=request,

        name="players.html",

        context={
            "current_user":
                current_user,

            "players":
                players,

            "asset_version":
                ASSET_VERSION,
        },
    )


@app.get(
    "/teams",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def teams_page(
    request: Request,

    current_user: UserRead = Depends(
        get_current_user
    ),

    service: TeamService = Depends(
        get_team_service
    ),

    player_service: PlayerService = Depends(
        get_player_service
    ),
):

    teams = await service.list(
        current_user.id
    )

    players = await player_service.list(
        current_user.id
    )


    return templates.TemplateResponse(
        request=request,

        name="teams.html",

        context={
            "current_user":
                current_user,

            "teams":
                teams,

            "players":
                players,

            "asset_version":
                ASSET_VERSION,
        },
    )


@app.get(
    "/trainings",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def trainings_page(
    request: Request,

    current_user: UserRead = Depends(
        get_current_user
    ),

    team_service: TeamService = Depends(
        get_team_service
    ),

    training_service: TrainingService = Depends(
        get_training_service
    ),
):

    teams = await team_service.list(
        current_user.id
    )

    selected_team = None

    raw_team_id = (
        request
        .query_params
        .get("team_id")
    )


    if (
        raw_team_id
        and raw_team_id.isdigit()
    ):

        candidate_id = int(
            raw_team_id
        )

        selected_team = next(
            (
                team
                for team in teams
                if team.id
                == candidate_id
            ),
            None,
        )


    if (
        selected_team is None
        and teams
    ):

        selected_team = teams[0]


    attendance_view = None


    if selected_team is not None:

        attendance_view = (
            await training_service
            .get_attendance_view(
                current_user.id,
                selected_team.id,
            )
        )


    return templates.TemplateResponse(
        request=request,

        name="trainings.html",

        context={
            "current_user":
                current_user,

            "teams":
                teams,

            "selected_team":
                selected_team,

            "attendance_view":
                attendance_view,

            "asset_version":
                ASSET_VERSION,
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

    current_user: UserRead = Depends(
        get_current_user
    ),

    team_service: TeamService = Depends(
        get_team_service
    ),

    training_service: TrainingService = Depends(
        get_training_service
    ),
):

    try:

        team = await team_service.get(
            current_user.id,
            team_id,
        )


        attendance_view = (
            await training_service
            .get_all_attendance_view(
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
            "current_user":
                current_user,

            "team":
                team,

            "attendance_view":
                attendance_view,

            "asset_version":
                ASSET_VERSION,
        },
    )


@app.post(
    "/trainings/attendance",
    response_model=AttendanceItemRead,
    include_in_schema=False,
)
async def web_upsert_attendance(
    payload: AttendanceUpsert,

    current_user: UserRead = Depends(
        get_current_user
    ),

    service: TrainingService = Depends(
        get_training_service
    ),
) -> AttendanceItemRead:

    try:

        return await (
            service
            .upsert_attendance(
                current_user.id,
                payload,
            )
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


@app.get(
    "/absence-reasons",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def absence_reasons_page(
    request: Request,

    current_user: UserRead = Depends(
        get_current_user
    ),

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
            "current_user":
                current_user,

            "reasons":
                reasons,

            "asset_version":
                ASSET_VERSION,
        },
    )


if __name__ == "__main__":

    uvicorn.run(
        "src.main:app",

        host=settings.HOST,

        port=settings.PORT,

        reload=settings.DEBUG,

        proxy_headers=True,

        forwarded_allow_ips=(
            settings
            .FORWARDED_ALLOW_IPS
        ),
    )
