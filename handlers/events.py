# Показ списку найближчих матчів та перехід до деталей конкретного матчу.

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from database import db
from keyboards import events_keyboard, outcome_keyboard

router = Router()


@router.message(Command("matches"))
async def cmd_matches(message: Message):
    events = await db.get_upcoming_events(limit=20)

    if not events:
        await message.answer(
            "Поки що немає доступних матчів. Можливо, їх ще не оновили - "
            "спробуй пізніше або скажи ЯрИку."
        )
        return

    await message.answer(
        "⚽ Найближчі матчі. Вибери, на який хочеш поставити почку:",
        reply_markup=events_keyboard(events),
    )


@router.callback_query(lambda c: c.data == "back_to_events")
async def back_to_events(callback: CallbackQuery):
    events = await db.get_upcoming_events(limit=20)
    await callback.message.edit_text(
        "⚽ Найближчі матчі. Вибери, на який хочеш поставити почку:",
        reply_markup=events_keyboard(events),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("event:"))
async def show_event(callback: CallbackQuery):
    event_id = int(callback.data.split(":")[1])
    event = await db.get_event_by_id(event_id)

    if event is None:
        await callback.answer("Матч не знайдено, можливо, його вже прибрали.", show_alert=True)
        return

    date_str = event.commence_time.strftime("%d.%m.%Y %H:%M")
    text = (
        f"⚽ <b>{event.home_team} — {event.away_team}</b>\n"
        f"🕒 {date_str}\n\n"
        f"Кеф:\n"
        f"П1 (перемога {event.home_team}) — {event.odds_home}\n"
        f"X (ниічия) — {event.odds_draw}\n"
        f"П2 (перемога {event.away_team}) — {event.odds_away}\n\n"
        f"Вибери результат, на який ставиш:"
    )

    await callback.message.edit_text(text, reply_markup=outcome_keyboard(event), parse_mode="HTML")
    await callback.answer()
