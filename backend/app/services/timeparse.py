import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

@dataclass
class TimeRange:
    start: datetime
    end: datetime


_WEEKDAY = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def parse_time_range(q: str) -> TimeRange | None:
    """
    Lightweight time intent parser (good enough for take-home).
    Returns UTC naive datetimes for filtering Document.created_at / source_published_at.
    """
    s = q.lower()

    now = datetime.utcnow()
    day_start = datetime(now.year, now.month, now.day)
    day_end = day_start + timedelta(days=1)

    if re.search(r"\btoday\b", s):
        return TimeRange(day_start, day_end)

    if re.search(r"\byesterday\b", s):
        y0 = day_start - timedelta(days=1)
        return TimeRange(y0, day_start)

    if re.search(r"\blast week\b", s):
        start = day_start - timedelta(days=7)
        return TimeRange(start, day_end)

    if re.search(r"\blast month\b", s):
        start = day_start - relativedelta(months=1)
        return TimeRange(start, day_end)

    m = re.search(r"\b(\d{4})\b", s)
    if m and ("in " + m.group(1)) in s:
        year = int(m.group(1))
        start = datetime(year, 1, 1)
        end = datetime(year + 1, 1, 1)
        return TimeRange(start, end)

    m2 = re.search(r"\blast\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", s)
    if m2:
        target = _WEEKDAY[m2.group(1)]
        delta = (day_start.weekday() - target) % 7
        delta = 7 if delta == 0 else delta
        start = day_start - timedelta(days=delta)
        end = start + timedelta(days=1)
        return TimeRange(start, end)

    return None