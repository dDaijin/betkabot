# Базові команди: /start (реєстрація), /balance, /leaderboard.

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from config import CURRENCY_NAME
from database import db

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    user = await db.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
    )
    await message.answer(
        f"Здароу, {message.from_user.first_name}! 👋\n\n"
        f"Це бот для ставок на віртуальну валюту - без реальних дєнєК."
        f"чисто перевірить удачу\n\n"
        f"Твій стартовий баланс: <b>{user.balance:.0f} {CURRENCY_NAME}</b>\n\n"
        f"Команди:\n"
        f"/matches — найближчі матчі та коефіцієнти\n"
        f"/balance — твій баланс\n"
        f"/mybets — твої ставки\n"
        f"/leaderboard — таблиця ПЕРЕМОжців",
        parse_mode="HTML",
    )


@router.message(Command("balance"))
async def cmd_balance(message: Message):
    user = await db.get_or_create_user(message.from_user.id, message.from_user.username)
    await message.answer(f"Твой баланс: <b>{user.balance:.0f} {CURRENCY_NAME}</b>", parse_mode="HTML")


@router.message(Command("leaderboard"))
async def cmd_leaderboard(message: Message):
    users = await db.get_leaderboard(limit=10)
    if not users:
        await message.answer("Поки що ніхто не зареєстрований.")
        return

    lines = ["🏆 <b>Таблиця лідерів</b>\n"]
    medals = ["🥇", "🥈", "🥉"]
    for i, user in enumerate(users):
        prefix = medals[i] if i < 3 else f"{i + 1}."
        name = user.username or f"id{user.telegram_id}"
        lines.append(f"{prefix} {name} — {user.balance:.0f} {CURRENCY_NAME}")

    await message.answer("\n".join(lines), parse_mode="HTML")
