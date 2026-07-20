
# Адмінські команди: підтягнути свіжі матчі з API, оновити результати завершених.


from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config import ADMIN_IDS, DEFAULT_SPORT_KEY
from database import db
from database.models import EventStatus
from services.odds_api import fetch_odds, fetch_scores, OddsApiError
from services.betting import resolve_event, outcome_from_scores

router = Router()


def _is_admin(telegram_id: int) -> bool:
    return telegram_id in ADMIN_IDS


@router.message(Command("update_matches"))
async def cmd_update_matches(message: Message):
    if not _is_admin(message.from_user.id):
        await message.answer("Но но но, тік для адміна.")
        return

    await message.answer("Шукаю матчі та кефи...")

    try:
        odds_events = await fetch_odds(DEFAULT_SPORT_KEY)
    except OddsApiError as e:
        await message.answer(f"Не вдалось отримати інфу з Odds API: {e}")
        return

    count = 0
    for oe in odds_events:
        await db.upsert_event(
            external_id=oe.external_id,
            sport_key=oe.sport_key,
            home_team=oe.home_team,
            away_team=oe.away_team,
            commence_time=oe.commence_time,
            odds_home=oe.odds_home,
            odds_draw=oe.odds_draw,
            odds_away=oe.odds_away,
        )
        count += 1

    await message.answer(f"Готово! Оновлено\Додано матчі: {count}")


@router.message(Command("check_results"))
async def cmd_check_results(message: Message):
    if not _is_admin(message.from_user.id):
        await message.answer("Для Одмема.")
        return

    await message.answer("Перевіряю результати(рахую бабки)...")

    try:
        scores_data = await fetch_scores(DEFAULT_SPORT_KEY)
    except OddsApiError as e:
        await message.answer(f"Не вдалось отримати результат: {e}")
        return

    upcoming_events = await db.get_upcoming_events(limit=100)
    upcoming_by_external_id = {e.external_id: e for e in upcoming_events}

    resolved_count = 0
    for raw in scores_data:
        if not raw.get("completed"):
            continue

        event = upcoming_by_external_id.get(raw["id"])
        if event is None:
            continue  # або вже закрито, або це не та ліга/матч у нас в базі

        scores = raw.get("scores")
        if not scores:
            continue

        # API дає рахунок як список {name, score} для кожної команди
        score_by_team = {s["name"]: int(s["score"]) for s in scores}
        home_score = score_by_team.get(event.home_team)
        away_score = score_by_team.get(event.away_team)

        if home_score is None or away_score is None:
            continue

        result = outcome_from_scores(home_score, away_score)
        summary = await resolve_event(event.id, result)
        resolved_count += 1

        await message.answer(
            f"⚽ {event.home_team} {home_score}:{away_score} {event.away_team}\n"
            f"Ставок выиграло: {summary['won']}, проиграло: {summary['lost']}, "
            f"выплачено: {summary['total_payout']:.0f}"
        )

    if resolved_count == 0:
        await message.answer("Нових завершених матчів не знайдено.")
    else:
        await message.answer(f"підСУМКИ по {resolved_count} матчам.")
