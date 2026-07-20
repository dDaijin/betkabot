
```markdown
# BetBot — Telegram Bot for Betting with Virtual Currency

A bot to play: bet on sports events without real money.
Odds are fetched from [The Odds API](https://the-odds-api.com/).

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt

```

2. Copy `.env.example` to `.env` and fill it out:
```bash
cp .env.example .env

```


* `BOT_TOKEN` — get it from [@BotFather](https://t.me/BotFather) (`/newbot`)
* `ODDS_API_KEY` — get it for free at [the-odds-api.com](https://the-odds-api.com/) (500 requests/month free)
* `ADMIN_IDS` — your telegram_id (can be found via [@userinfobot](https://t.me/userinfobot)), separated by commas if there are multiple admins


3. Run the bot:
```bash
python bot.py

```

## How to Use

**Regular User:**

* `/start` — registration, gives a starting balance (1000 coins)
* `/matches` — list of upcoming matches with odds, allows making a bet
* `/balance` — current balance
* `/mybets` — your betting history
* `/leaderboard` — leaderboard among all players

**Administrator (telegram_id from ADMIN_IDS):**

* `/update_matches` — fetch fresh matches and odds from The Odds API
* `/check_results` — check results of finished matches and automatically calculate bets

## Future Enhancements / To-Do

* Automate `/update_matches` and `/check_results` on a schedule (using `apscheduler` or cron) so you don't have to trigger them manually
* Add more sports — change/expand `DEFAULT_SPORT_KEY` in `config.py` (list of keys: https://the-odds-api.com/sports-odds-data/sports-apis.html)
* Allow choosing a league/sport directly inside the bot, rather than relying only on the default one from the config
* Prevent betting on matches that have already started (compare `commence_time` with current time before confirming a bet)
* Set minimum/maximum bet limits

## Project Structure

```
betbot/
├── bot.py                 # entry point
├── config.py               # settings from .env
├── database/
│   ├── models.py           # User, Event, Bet models
│   └── db.py                # DB connection and operations
├── services/
│   ├── odds_api.py          # requests to The Odds API
│   └── betting.py           # bet calculation, payouts
├── handlers/
│   ├── start.py              # /start, /balance, /leaderboard
│   ├── events.py             # /matches, viewing a match
│   ├── bets.py                # placing a bet
│   ├── results.py            # /mybets
│   └── admin.py               # /update_matches, /check_results
└── keyboards.py             # inline keyboards

```
