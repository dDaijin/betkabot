# Inline-клавіатури: список матчів, вибір результату, вибір суми ставки.
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.models import Event, Outcome

# Фіксовані варіанти суми ставки - простіше для UX, ніж просити вводити число руками
QUICK_AMOUNTS = [50, 100, 250, 500]


def events_keyboard(events: list[Event]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for event in events:
        date_str = event.commence_time.strftime("%d.%m %H:%M")
        text = f"{event.home_team} – {event.away_team} ({date_str})"
        builder.row(InlineKeyboardButton(text=text, callback_data=f"event:{event.id}"))
    return builder.as_markup()


def outcome_keyboard(event: Event) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=f"П1 ({event.odds_home})", callback_data=f"outcome:{event.id}:home"),
        InlineKeyboardButton(text=f"X ({event.odds_draw})", callback_data=f"outcome:{event.id}:draw"),
        InlineKeyboardButton(text=f"П2 ({event.odds_away})", callback_data=f"outcome:{event.id}:away"),
    )
    builder.row(InlineKeyboardButton(text="« Назад до матчІв", callback_data="back_to_events"))
    return builder.as_markup()


def amount_keyboard(event_id: int, outcome: Outcome) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    row = [
        InlineKeyboardButton(text=f"{amount}", callback_data=f"amount:{event_id}:{outcome.value}:{amount}")
        for amount in QUICK_AMOUNTS
    ]
    builder.row(*row)
    builder.row(
        InlineKeyboardButton(text="Своя сума", callback_data=f"custom_amount:{event_id}:{outcome.value}")
    )
    builder.row(InlineKeyboardButton(text="« Назад", callback_data=f"event:{event_id}"))
    return builder.as_markup()
