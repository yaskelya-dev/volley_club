import asyncio
import os
import subprocess
from typing import Final

from sqlalchemy import text

from src.database.database import async_engine


# Один advisory lock для всех экземпляров приложения.
MIGRATION_LOCK_ID: Final[int] = 741852963


async def run_migrations_with_lock() -> None:
    """
    Берём advisory-lock в отдельной PostgreSQL-сессии.

    Если одновременно стартуют несколько app-контейнеров,
    только один выполняет Alembic, остальные ждут освобождения lock.
    """
    async with async_engine.connect() as connection:

        await connection.execute(
            text(
                "SELECT pg_advisory_lock(:lock_id)"
            ),
            {
                "lock_id": MIGRATION_LOCK_ID
            },
        )

        await connection.commit()


        try:

            result = await asyncio.to_thread(
                subprocess.run,
                [
                    "alembic",
                    "upgrade",
                    "head",
                ],
                check=False,
            )


            if result.returncode != 0:
                raise SystemExit(
                    "Alembic migration failed "
                    "with exit code "
                    f"{result.returncode}"
                )

        finally:

            await connection.execute(
                text(
                    "SELECT pg_advisory_unlock(:lock_id)"
                ),
                {
                    "lock_id":
                        MIGRATION_LOCK_ID
                },
            )

            await connection.commit()


async def main() -> None:
    await run_migrations_with_lock()

    # После миграции заменяем entrypoint на сам Python-процесс.
    # Docker получает правильный PID 1 и сигналы SIGTERM/SIGINT.
    os.execvp(
        "python3",
        [
            "python3",
            "-m",
            "src.main",
        ],
    )


if __name__ == "__main__":
    asyncio.run(main())
