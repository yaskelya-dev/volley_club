from django.core.management.base import BaseCommand
import asyncio
from bot import main


class Command(BaseCommand):
    help = 'Запуск Telegram бота'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Запуск Telegram бота...'))
        asyncio.run(main())
