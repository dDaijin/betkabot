
```python
"""
BetBot Configuration Module.

Reads environment variables from the .env file and sets core application settings.

===============================================================================
SYSTEM ARCHITECTURE & LOGIC (Mermaid)
===============================================================================

1. High-Level Architecture Diagram:
```mermaid
graph TD
    A[Telegram User] <-->|Messages / Commands| B[Telegram Bot API]
    B <-->|Bot Framework| C[BetBot Core Application]
    
    subgraph Core Application
        C --> D[Handlers / Controllers]
        D --> E[Betting Service]
        D --> F[Odds API Client]
        D --> G[Database Layer]
    end

    F <-->|HTTP Requests| H[External Odds API]
    G <-->|CRUD Operations| I[(SQLite DB: betbot.db)]

```

2. Entity Relationship Diagram (ERD):

```mermaid
erDiagram
    USERS ||--o{ BETS : places
    MATCHES ||--o{ BETS : targets

    USERS {
        int telegram_id PK
        string username
        decimal virtual_balance "Initial: 1000 shekels"
        datetime created_at
    }

    BETS {
        int id PK
        int user_id FK
        int match_id FK
        string selected_outcome
        decimal odds
        decimal bet_amount
        string status "pending / won / lost"
        datetime created_at
    }

    MATCHES {
        int id PK
        string external_match_id
        string home_team
        string away_team
        datetime start_time
        string status "upcoming / finished"
        string result
    }

```

===============================================================================
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

# Comma-separated Admin Telegram IDs in .env, e.g.: ADMIN_IDS=123456789,987654321

_admin_ids_raw = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(x.strip()) for x in _admin_ids_raw.split(",") if x.strip()]

START_BALANCE = 1000

CURRENCY_NAME = "shekels"

# Path to the SQLite database file

DB_PATH = "betbot.db"

# Default sport key fetched from The Odds API.

# See available sport keys here: https://the-odds-api.com/sports-odds-data/sports-apis.html

# soccer_fifa_world_cup — World Cup, can be changed/extended later

DEFAULT_SPORT_KEY = "soccer_fifa_world_cup"

# Bookmaker region to fetch odds for (eu — European bookmakers)

ODDS_REGION = "eu"

if not BOT_TOKEN:
raise RuntimeError(
"BOT_TOKEN not found. Create a .env file based on .env.example and add your bot token."
)

```

```
