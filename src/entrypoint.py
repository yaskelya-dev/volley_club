import asyncio
import os

from src.database.migration_runner import run_migrations_with_lock


async def main() -> None:
    await run_migrations_with_lock()
    # Replace entrypoint with Python so PID 1 receives container signals.
    os.execvp("python3", ["python3", "-m", "src.main"])


if __name__ == "__main__":
    asyncio.run(main())
