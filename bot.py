import os
import django
import asyncio
import logging
from volley_club import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'volley_club.settings')
django.setup()

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from users.models import CustomUser, TelegramVerificationCode

BOT_TOKEN = settings.TG_BOT_TOKEN
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def handle_start(message: types.Message):
    tg_username = message.from_user.username

    if not tg_username:
        await message.answer("У вас не заполнен @username в настройках Telegram.")
        return

    # Запрос к общей базе данных PostgreSQL
    try:
        user = await CustomUser.objects.aget(telegram_username__iexact=tg_username)

        # Запоминаем telegram_id пользователя
        user.telegram_id = message.from_user.id
        await user.asave()  # <--- 1. Асинхронное сохранение

        # Ищем сгенерированный на сайте код
        # <--- 2. Асинхронное получение первого элемента (afirst)
        verification_entry = await TelegramVerificationCode.objects.filter(user=user).afirst()

        if verification_entry:
            await message.answer(
                f"Ваш код для подтверждения профиля на сайте:\n\n"
                f"<code>{verification_entry.code}</code>",
                parse_mode="HTML"
            )
        else:
            await message.answer("Код подтверждения не найден. Запросите его повторно в профиле на сайте.")

    except CustomUser.DoesNotExist:
        await message.answer("Пользователь с таким Telegram никнеймом не найден на сайте.")


async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
