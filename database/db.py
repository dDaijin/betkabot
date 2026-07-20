"""
Подключение к базе данных и базовые операции (репозиторий-стиль).
Используем async SQLAlchemy с aiosqlite — подходит под асинхронный aiogram.
"""
from contextlib import asynccontextmanager
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from config import DB_PATH, START_BALANCE
from database.models import Base, User, Event, Bet, EventStatus, BetStatus, Outcome

engine = create_async_engine(f"sqlite+aiosqlite:///{DB_PATH}")
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def init_db() -> None:
    """Создаёт таблицы, если их ещё нет. Вызывается один раз при старте бота."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def get_session():
    async with async_session() as session:
        yield session


# ---------- Пользователи ----------

async def get_or_create_user(telegram_id: int, username: str | None) -> User:
    """Возвращает пользователя, создавая его с стартовым балансом при первом обращении."""
    async with get_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if user:
            return user

        user = User(telegram_id=telegram_id, username=username, balance=START_BALANCE)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


async def get_user_by_telegram_id(telegram_id: int) -> User | None:
    async with get_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()


async def update_balance(user_id: int, delta: float) -> None:
    """Изменяет баланс пользователя на delta (может быть отрицательным)."""
    async with get_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one()
        user.balance = round(user.balance + delta, 2)
        await session.commit()


async def get_leaderboard(limit: int = 10) -> list[User]:
    async with get_session() as session:
        result = await session.execute(
            select(User).order_by(User.balance.desc()).limit(limit)
        )
        return list(result.scalars().all())


# ---------- События ----------

async def upsert_event(
    external_id: str,
    sport_key: str,
    home_team: str,
    away_team: str,
    commence_time: datetime,
    odds_home: float,
    odds_draw: float,
    odds_away: float,
) -> Event:
    """Создаёт событие или обновляет коэффициенты, если событие уже есть."""
    async with get_session() as session:
        result = await session.execute(select(Event).where(Event.external_id == external_id))
        event = result.scalar_one_or_none()

        if event:
            # Не трогаем коэффициенты завершённых/отменённых событий
            if event.status == EventStatus.UPCOMING:
                event.odds_home = odds_home
                event.odds_draw = odds_draw
                event.odds_away = odds_away
                event.commence_time = commence_time
        else:
            event = Event(
                external_id=external_id,
                sport_key=sport_key,
                home_team=home_team,
                away_team=away_team,
                commence_time=commence_time,
                odds_home=odds_home,
                odds_draw=odds_draw,
                odds_away=odds_away,
            )
            session.add(event)

        await session.commit()
        await session.refresh(event)
        return event


async def get_upcoming_events(limit: int = 20) -> list[Event]:
    async with get_session() as session:
        result = await session.execute(
            select(Event)
            .where(Event.status == EventStatus.UPCOMING)
            .order_by(Event.commence_time.asc())
            .limit(limit)
        )
        return list(result.scalars().all())


async def get_event_by_id(event_id: int) -> Event | None:
    async with get_session() as session:
        result = await session.execute(select(Event).where(Event.id == event_id))
        return result.scalar_one_or_none()


# ---------- Ставки ----------

async def place_bet(user_id: int, event_id: int, outcome: Outcome, amount: float, odds: float) -> Bet:
    async with get_session() as session:
        bet = Bet(
            user_id=user_id,
            event_id=event_id,
            outcome=outcome,
            amount=amount,
            odds_at_bet_time=odds,
            status=BetStatus.PENDING,
        )
        session.add(bet)
        await session.commit()
        await session.refresh(bet)
        return bet


async def get_user_bets(user_id: int, status: BetStatus | None = None) -> list[Bet]:
    async with get_session() as session:
        query = select(Bet).where(Bet.user_id == user_id)
        if status:
            query = query.where(Bet.status == status)
        query = query.order_by(Bet.created_at.desc())
        result = await session.execute(query)
        return list(result.scalars().all())


async def get_pending_bets_for_event(event_id: int) -> list[Bet]:
    async with get_session() as session:
        result = await session.execute(
            select(Bet).where(Bet.event_id == event_id, Bet.status == BetStatus.PENDING)
        )
        return list(result.scalars().all())
