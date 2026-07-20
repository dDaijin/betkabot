# Логіка розрахунку ставок: визначення результату матчу та закриття пов'язаних ставок.

from sqlalchemy import select

from database.models import Outcome, BetStatus, EventStatus, Event, Bet, User
from database import db


async def resolve_event(event_id: int, result: Outcome) -> dict:
    # Закриває подію із зазначеним результатом і розраховує всі очікувані ставки на неї.
    # Повертає зведення: скільки ставок виграло/програло і яку суму.
    summary = {"won": 0, "lost": 0, "total_payout": 0.0}

    async with db.get_session() as session:
        db_event = (await session.execute(select(Event).where(Event.id == event_id))).scalar_one_or_none()
        if db_event is None:
            raise ValueError(f"Событие {event_id} не знайдено")

        db_event.status = EventStatus.FINISHED
        db_event.result = result

        bets_result = await session.execute(
            select(Bet).where(Bet.event_id == event_id, Bet.status == BetStatus.PENDING)
        )
        pending_bets = list(bets_result.scalars().all())

        for db_bet in pending_bets:
            if db_bet.outcome == result:
                payout = db_bet.potential_payout
                db_bet.status = BetStatus.WON
                summary["won"] += 1
                summary["total_payout"] += payout

                user = (await session.execute(select(User).where(User.id == db_bet.user_id))).scalar_one()
                user.balance = round(user.balance + payout, 2)
            else:
                db_bet.status = BetStatus.LOST
                summary["lost"] += 1

        await session.commit()

    return summary


async def cancel_event(event_id: int) -> int:
    # Скасовує подію та повертає гроші за всіма очікуваними ставками. Повертає кількість повернень.
    async with db.get_session() as session:
        db_event = (await session.execute(select(Event).where(Event.id == event_id))).scalar_one_or_none()
        if db_event is None:
            raise ValueError(f"ПОдія {event_id} не знайдено")

        db_event.status = EventStatus.CANCELLED

        bets_result = await session.execute(
            select(Bet).where(Bet.event_id == event_id, Bet.status == BetStatus.PENDING)
        )
        pending_bets = list(bets_result.scalars().all())

        for db_bet in pending_bets:
            db_bet.status = BetStatus.REFUNDED
            user = (await session.execute(select(User).where(User.id == db_bet.user_id))).scalar_one()
            user.balance = round(user.balance + db_bet.amount, 2)

        await session.commit()
        return len(pending_bets)


def outcome_from_scores(home_score: int, away_score: int) -> Outcome:
    # Визначає результат 1X2 за підсумковим рахунком матчу.
    if home_score > away_score:
        return Outcome.HOME
    if home_score < away_score:
        return Outcome.AWAY
    return Outcome.DRAW

