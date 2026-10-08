from src.api.v1.absence_reasons import (
    router as absence_reasons_router,
)
from src.api.v1.attendance import (
    router as attendance_router,
)
from src.api.v1.players import (
    router as players_router,
)
from src.api.v1.teams import (
    router as teams_router,
)
from src.api.v1.trainings import (
    router as trainings_router,
)
from src.api.v1.users import (
    router as users_router,
)


__all__ = [
    "users_router",
    "players_router",
    "teams_router",
    "trainings_router",
    "attendance_router",
    "absence_reasons_router",
]
