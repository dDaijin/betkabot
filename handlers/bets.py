
# Оформлення ставки: вибір суми (швидкі кнопки або сума через FSM), списання балансу.

from aiogram import Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from config import CURRENCY_NAME
from database import db
from database.models import Outcome
from keyboards import amount_keyboard

router = Router()

OUTCOME_LABELS = {Outcome.HOME: "П1", Outcome.DRAW: "X", Outcome.AWAY: "П2"}


class BetStates(StatesGroup):
    waiting_for_amount = State()


@router.callback_query(lambda c: c.data.startswith("outcome:"))
async def choose_amount(callback: CallbackQuery):
    _, event_id, outcome_value = callback.data.split(":")
    event_id = int(event_id)
    outcome = Outcome(outcome_value)

    event = await db.get_event_by_id(event_id)
    if event is None:
        await callback.answer("Матч не знайшов.", show_alert=True)
        return

    odds = {"home": event.odds_home, "draw": event.odds_draw, "away": event.odds_away}[outcome_value]

    text = (
        f"Ставка: <b>{OUTCOME_LABELS[outcome]}</b> "
        f"({event.home_team} — {event.away_team})\n"
        f"Коефіцієнт: {odds}\n\n"
        f"Обери суму ставки в {CURRENCY_NAME}:"
    )
    await callback.message.edit_text(text, reply_markup=amount_keyboard(event_id, outcome), parse_mode="HTML")
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("amount:"))
async def confirm_quick_amount(callback: CallbackQuery):
    _, event_id, outcome_value, amount = callback.data.split(":")
    await _place_bet(callback, int(event_id), Outcome(outcome_value), float(amount))


@router.callback_query(lambda c: c.data.startswith("custom_amount:"))
async def ask_custom_amount(callback: CallbackQuery, state: FSMContext):
    _, event_id, outcome_value = callback.data.split(":")
    await state.update_data(event_id=int(event_id), outcome=outcome_value)
    await state.set_state(BetStates.waiting_for_amount)

    await callback.message.edit_text(
        f"Введи суму ставки в {CURRENCY_NAME} числом (наприклад: 150):"
    )
    await callback.answer()


@router.message(StateFilter(BetStates.waiting_for_amount))
async def receive_custom_amount(message: Message, state: FSMContext):
    text = message.text.strip().replace(",", ".")

    try:
        amount = float(text)
    except ValueError:
        await message.answer("Йолоп, це не число. Введи сумму ставки числом, наприклад: 150")
        return

    if amount <= 0:
        await message.answer("Більше нуля... оболтус.")
        return

    data = await state.get_data()
    await state.clear()

    await _place_bet_from_message(message, data["event_id"], Outcome(data["outcome"]), amount)


async def _place_bet(callback: CallbackQuery, event_id: int, outcome: Outcome, amount: float):
    result_text = await _execute_bet(callback.from_user.id, callback.from_user.username, event_id, outcome, amount)
    await callback.message.edit_text(result_text, parse_mode="HTML")
    await callback.answer()


async def _place_bet_from_message(message: Message, event_id: int, outcome: Outcome, amount: float):
    result_text = await _execute_bet(message.from_user.id, message.from_user.username, event_id, outcome, amount)
    await message.answer(result_text, parse_mode="HTML")


async def _execute_bet(telegram_id: int, username: str | None, event_id: int, outcome: Outcome, amount: float) -> str:
    # Загальна логіка перевірки балансу, списання та створення ставки. Повертає текст користувача.
    user = await db.get_or_create_user(telegram_id, username)
    event = await db.get_event_by_id(event_id)

    if event is None:
        return "Немона більш поставить((("

    if event.status.value != "upcoming":
        return "Вже почався, або завершився, тому неможна більш ставить сюда"

    if user.balance < amount:
        return (
            f"Грошиків нема( {user.balance:.0f} {CURRENCY_NAME}, "
            f"а ставка — {amount:.0f}."
        )

    odds = {"home": event.odds_home, "draw": event.odds_draw, "away": event.odds_away}[outcome.value]

    await db.update_balance(user.id, -amount)
    bet = await db.place_bet(user.id, event.id, outcome, amount, odds)

    return (
        f"✅ Ставочка прийнята!\n\n"
        f"{event.home_team} — {event.away_team}\n"
        f"Результат: {OUTCOME_LABELS[outcome]} (коэф. {odds})\n"
        f"Сума: {amount:.0f} {CURRENCY_NAME}\n"
        f"МОжеш виграть: {bet.potential_payout:.0f} {CURRENCY_NAME}\n\n"
        f"Новий баланс: {(user.balance - amount):.0f} {CURRENCY_NAME}"
    )
