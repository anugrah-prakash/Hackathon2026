"""Deterministic display helpers; never infer dates or years."""
import re
from datetime import date

MONTHS = ('January February March April May June July August September October November December').split()


def deadline_label(value):
    if value is None:
        return 'Not clearly stated. Ask the sender to confirm.'
    # Only convert a standalone absolute date, optionally preceded by German 'by'.
    # Keep relative deadlines, conditions, ranges and other text exactly as supplied.
    match = re.fullmatch(r'\s*(?:bis\s+(?:zum\s+)?)?(\d{1,2})\.(\d{1,2})\.(\d{4})\s*', value)
    if not match:
        return value
    day, month, year = map(int, match.groups())
    try:
        date(year, month, day)
    except ValueError:
        return value
    return f'By {day} {MONTHS[month - 1]} {year}'
