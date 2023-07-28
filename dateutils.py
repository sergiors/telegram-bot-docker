from datetime import datetime

import pendulum


def now(tz: str = 'America/Sao_Paulo') -> datetime:
    return pendulum.now(tz)


def iso(dt: datetime) -> str:
    return dt.isoformat()
