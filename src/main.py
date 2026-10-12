from contextlib import asynccontextmanager
import hashlib
from pathlib import Path
from typing import AsyncIterator
from urllib.parse import quote

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from src.api.web import router as web_router
from src.api.v1 import (
    absence_reasons_router,
    attendance_router,
    players_router,
    teams_router,
    trainings_router,
    users_router,
)
from src.core.config import settings
from src.database.database import async_engine

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_CSS = STATIC_DIR / "css" / "style.css"

if not STATIC_CSS.is_file():
    raise RuntimeError(f"Static CSS is missing: {STATIC_CSS}")

_asset_digest = hashlib.sha256()
for _asset_path in (
    STATIC_CSS,
    STATIC_DIR / "css" / "responsive-overrides.css",
):
    if _asset_path.is_file():
        _asset_digest.update(_asset_path.read_bytes())
ASSET_VERSION = _asset_digest.hexdigest()[:12]


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
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

# Shared Jinja environment and asset version are used by the HTML router and
# exception handlers; there is only one template/static configuration.
templates = Jinja2Templates(directory=TEMPLATES_DIR)
app.state.templates = templates
app.state.asset_version = ASSET_VERSION

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Browser pages and the legacy browser attendance endpoint keep their URLs.
app.include_router(web_router)

# Existing versioned JSON APIs stay mounted under the same prefix.
for api_router in (
    users_router,
    players_router,
    teams_router,
    trainings_router,
    attendance_router,
    absence_reasons_router,
):
    app.include_router(api_router, prefix="/api/v1")


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
):
    path = request.url.path
    content_type = request.headers.get("content-type", "").lower()
    accept = request.headers.get("accept", "").lower()
    is_api_request = (
        path == "/api"
        or path.startswith("/api/")
        or "application/json" in content_type
        or "application/json" in accept
    )
    is_static_request = path == "/static" or path.startswith("/static/")
    accepts_html = "text/html" in accept

    if (
        exc.status_code == 401
        and accepts_html
        and not is_api_request
        and not is_static_request
    ):
        next_url = request.url.path
        if request.url.query:
            next_url = f"{next_url}?{request.url.query}"
        return RedirectResponse(
            url=f"/login?next={quote(next_url, safe='')}",
            status_code=303,
        )

    if (
        exc.status_code == 404
        and accepts_html
        and not is_api_request
        and not is_static_request
    ):
        return templates.TemplateResponse(
            request=request,
            name="404.html",
            context={"current_user": None, "asset_version": ASSET_VERSION},
            status_code=404,
        )

    # Preserve JSON errors for API/fetch clients and all other HTTP errors.
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )


@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        proxy_headers=True,
        forwarded_allow_ips=settings.FORWARDED_ALLOW_IPS,
    )
