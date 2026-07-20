# Моделі баз даних.

# User – гравець: його telegram_id та баланс віртуальної валюти.
# Event – ​​спортивна подія (матч) з коефіцієнтами, підтягнутими з API.
# Bet - Ставка користувача на конкретний результат події.

from datetime import datetime
from enum import Enum

from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class EventStatus(str, Enum):
    UPCOMING = "upcoming"      
    FINISHED = "finished"      
    CANCELLED = "cancelled"    


class Outcome(str, Enum):
    HOME = "home"   
    DRAW = "draw"   
    AWAY = "away"  


class BetStatus(str, Enum):
    PENDING = "pending"   
    WON = "won"          
    LOST = "lost"         
    REFUNDED = "refunded"  


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    balance: Mapped[float] = mapped_column(Float, default=1000.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    bets: Mapped[list["Bet"]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"<User {self.telegram_id} balance={self.balance}>"


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    # ID события из The Odds API — по нему обновляем коэффициенты/результат
    external_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    sport_key: Mapped[str] = mapped_column(String(64))
    home_team: Mapped[str] = mapped_column(String(128))
    away_team: Mapped[str] = mapped_column(String(128))
    commence_time: Mapped[datetime] = mapped_column(DateTime)

    # Коефіцієнти на момент останнього оновлення з API
    odds_home: Mapped[float] = mapped_column(Float)
    odds_draw: Mapped[float] = mapped_column(Float)
    odds_away: Mapped[float] = mapped_column(Float)

    status: Mapped[EventStatus] = mapped_column(SAEnum(EventStatus), default=EventStatus.UPCOMING)
    # Підсумковий результат заповнюється після завершення матчу
    result: Mapped[Outcome | None] = mapped_column(SAEnum(Outcome), nullable=True)

    bets: Mapped[list["Bet"]] = relationship(back_populates="event")

    def __repr__(self) -> str:
        return f"<Event {self.home_team} vs {self.away_team} ({self.status})>"


class Bet(Base):
    __tablename__ = "bets"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"))

    outcome: Mapped[Outcome] = mapped_column(SAEnum(Outcome))
    amount: Mapped[float] = mapped_column(Float)
    # Коефіцієнт фіксується на момент ставки і більше не змінюється,
    # навіть якщо у букмекера він потім накриється
    odds_at_bet_time: Mapped[float] = mapped_column(Float)

    status: Mapped[BetStatus] = mapped_column(SAEnum(BetStatus), default=BetStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="bets")
    event: Mapped["Event"] = relationship(back_populates="bets")

    @property
    def potential_payout(self) -> float:
        """Сколько получит игрок, если ставка зайдёт (включая саму ставку)."""
        return round(self.amount * self.odds_at_bet_time, 2)

    def __repr__(self) -> str:
        return f"<Bet user={self.user_id} event={self.event_id} {self.outcome} {self.amount}@{self.odds_at_bet_time}>"
