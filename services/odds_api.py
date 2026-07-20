
# Сервіс для отримання матчів та коефіцієнтів з The Odds API.
# Документація: https://the-odds-api.com/liveapi/guides/v4/

from datetime import datetime
from dataclasses import dataclass

import httpx

from config import ODDS_API_KEY, DEFAULT_SPORT_KEY, ODDS_REGION

BASE_URL = "https://api.the-odds-api.com/v4"


@dataclass
class OddsEvent:
    # Спрощене подання події з коефіцієнтами 1X2 (середнє за букмекерами).
    external_id: str
    sport_key: str
    home_team: str
    away_team: str
    commence_time: datetime
    odds_home: float
    odds_draw: float
    odds_away: float


class OddsApiError(Exception):
    pass


async def fetch_odds(sport_key: str = DEFAULT_SPORT_KEY) -> list[OddsEvent]:
    # Тягне найближчі події з коефіцієнтами на перемогу/нічию/перемогу (h2h ринок).
    # Якщо у різних букмекерів різні коефіцієнти – беремо середнє за доступними.
    if not ODDS_API_KEY:
        raise OddsApiError("ODDS_API_KEY не задан в .env")

    params = {
        "apiKey": ODDS_API_KEY,
        "regions": ODDS_REGION,
        "markets": "h2h",
        "oddsFormat": "decimal",
    }

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(f"{BASE_URL}/sports/{sport_key}/odds", params=params)

    if response.status_code != 200:
        raise OddsApiError(f"Odds API повернув помилку {response.status_code}: {response.text}")

    raw_events = response.json()
    events: list[OddsEvent] = []

    for raw in raw_events:
        home_team = raw.get("home_team")
        away_team = raw.get("away_team")
        bookmakers = raw.get("bookmakers", [])

        if not bookmakers:
            continue  # немає коефіцієнтів від букмекерів - пропускаємо матч

        home_odds, draw_odds, away_odds = _average_h2h_odds(bookmakers, home_team, away_team)
        if home_odds is None:
            continue  # не вдалося розпарити ринок h2h для цієї події

        events.append(
            OddsEvent(
                external_id=raw["id"],
                sport_key=sport_key,
                home_team=home_team,
                away_team=away_team,
                commence_time=datetime.fromisoformat(raw["commence_time"].replace("Z", "+00:00")),
                odds_home=round(home_odds, 2),
                odds_draw=round(draw_odds, 2),
                odds_away=round(away_odds, 2),
            )
        )

    return events


def _average_h2h_odds(
    bookmakers: list[dict], home_team: str, away_team: str
) -> tuple[float | None, float | None, float | None]:
    # Вважає середній коефіцієнт за всіма букмекерами для результатів П1/X/П2.
    home_prices, draw_prices, away_prices = [], [], []

    for bookmaker in bookmakers:
        for market in bookmaker.get("markets", []):
            if market.get("key") != "h2h":
                continue
            for outcome in market.get("outcomes", []):
                name = outcome.get("name")
                price = outcome.get("price")
                if name == home_team:
                    home_prices.append(price)
                elif name == away_team:
                    away_prices.append(price)
                elif name == "Draw":
                    draw_prices.append(price)

    if not home_prices or not away_prices or not draw_prices:
        return None, None, None

    return (
        sum(home_prices) / len(home_prices),
        sum(draw_prices) / len(draw_prices),
        sum(away_prices) / len(away_prices),
    )


async def fetch_scores(sport_key: str = DEFAULT_SPORT_KEY, days_from: int = 1) -> list[dict]:
    # Тягне результати завершених матчів за останні days_from днів.
    # Використовується для автоматичного закриття ставки.
    if not ODDS_API_KEY:
        raise OddsApiError("ODDS_API_KEY не задан в .env")

    params = {
        "apiKey": ODDS_API_KEY,
        "daysFrom": days_from,
    }

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(f"{BASE_URL}/sports/{sport_key}/scores", params=params)

    if response.status_code != 200:
        raise OddsApiError(f"Odds API вернул ошибку {response.status_code}: {response.text}")

    return response.json()
