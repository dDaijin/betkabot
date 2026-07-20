# Перегляд користувачем своїх ставок.
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config import CURRENCY_NAME
from database import db
from database.models import BetStatus

router = Router()

STATUS_LABELS = {
    BetStatus.PENDING: "⏳ чекаююю",
    BetStatus.WON: "✅ ПЕРЕМОГА!!!",
    BetStatus.LOST: "❌ НЕ БУДЕ ПЕРЕМОГИ(",
    BetStatus.REFUNDED: "↩️ повернено",
}
OUTCOME_LABELS = {"home": "П1", "draw": "X", "away": "П2"}


@router.message(Command("mybets"))
async def cmd_mybets(message: Message):
    user = await db.get_or_create_user(message.from_user.id, message.from_user.username)
    bets = await db.get_user_bets(user.id)

    if not bets:
        await message.answer("У тебе поки що немає ставок. Подивися /matches, щоб вибрати матч.")
        return

    lines = ["📋 <b>Твої ставки</b>\n"]
    for bet in bets[:20]:  # останні 20, щоб не спамати чат
        event = await db.get_event_by_id(bet.event_id)
        match_name = f"{event.home_team} — {event.away_team}" if event else "матч видалений"
        outcome_label = OUTCOME_LABELS.get(bet.outcome.value, bet.outcome.value)

        lines.append(
            f"{match_name}\n"
            f"  {outcome_label} | {bet.amount:.0f} {CURRENCY_NAME} "
            f"(коеф. {bet.odds_at_bet_time}) — {STATUS_LABELS[bet.status]}"
        )

    await message.answer("\n".join(lines), parse_mode="HTML")
