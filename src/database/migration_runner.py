import asyncio
import subprocess
from typing import Final

from sqlalchemy import text

from src.database.database import async_engine

# Shared advisory lock ID for every application container.
MIGRATION_LOCK_ID: Final[int] = 741852963


async def run_migrations_with_lock() -> None:
    """Acquire a PostgreSQL advisory lock, migrate, then release the lock."""
    async with async_engine.connect() as connection:
        await connection.execute(
            text("SELECT pg_advisory_lock(:lock_id)"),
            {"lock_id": MIGRATION_LOCK_ID},
        )
        await connection.commit()

        try:
            result = await asyncio.to_thread(
                subprocess.run,
                ["alembic", "upgrade", "head"],
                check=False,
            )
            if result.returncode != 0:
                raise SystemExit(
                    "Alembic migration failed with exit code "
                    f"{result.returncode}"
                )
        finally:
            await connection.execute(
                text("SELECT pg_advisory_unlock(:lock_id)"),
                {"lock_id": MIGRATION_LOCK_ID},
            )
            await connection.commit()
