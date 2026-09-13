"""Gregorian and Hijri calendar helpers for SmartStock AI."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

import pandas as pd
from hijri_converter import Gregorian


def get_next_week_dates(start_date: date | datetime | str | None = None) -> pd.DatetimeIndex:
    """Return the seven calendar days beginning on the next Monday.

    A Monday input intentionally returns the *following* Monday, making this
    suitable for planning the next complete business week.
    """
    reference = _to_date(start_date) if start_date is not None else date.today()
    days_until_monday = 7 - reference.weekday()  # Monday is 0; therefore Monday -> 7.
    next_monday = reference + timedelta(days=days_until_monday)
    return pd.date_range(start=next_monday, periods=7, freq="D")


def enrich_calendar_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add Gregorian and Hijri features to a DataFrame containing ``date``.

    The input is not mutated. Invalid or missing dates yield ``NaN`` for date
    features and ``False`` for event flags, so downstream dashboards remain
    usable while data-quality problems are easy to identify.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("enrich_calendar_features expects a pandas DataFrame.")
    if "date" not in df.columns:
        raise ValueError("The DataFrame must contain a 'date' column.")

    enriched = df.copy()
    dates = pd.to_datetime(enriched["date"], errors="coerce")
    enriched["date"] = dates
    enriched["day_of_week"] = dates.dt.day_name()
    enriched["is_weekend"] = dates.dt.dayofweek.isin([5, 6])
    enriched["month"] = dates.dt.month

    hijri_values = dates.map(_convert_timestamp_to_hijri)
    enriched["hijri_day"] = hijri_values.map(lambda value: value[0] if value else pd.NA).astype("Int64")
    enriched["hijri_month"] = hijri_values.map(lambda value: value[1] if value else pd.NA).astype("Int64")
    enriched["hijri_year"] = hijri_values.map(lambda value: value[2] if value else pd.NA).astype("Int64")
    enriched["is_ramadan"] = enriched["hijri_month"].eq(9).fillna(False).astype(bool)
    enriched["is_eid"] = enriched["hijri_month"].isin([10, 12]).astype(bool)
    return enriched


def convert_gregorian_to_hijri_string(date_obj: date | datetime | pd.Timestamp | str) -> str:
    """Return a Streamlit-friendly Hijri date, for example ``01 Ramadan 1447 AH``."""
    value = _to_date(date_obj)
    try:
        hijri = Gregorian(value.year, value.month, value.day).to_hijri()
    except (ValueError, OverflowError) as exc:
        raise ValueError(f"Could not convert {value.isoformat()} to a Hijri date.") from exc
    month_name = _HIJRI_MONTH_NAMES[hijri.month - 1]
    return f"{hijri.day:02d} {month_name} {hijri.year} AH"


def gregorian_to_hijri(value: date) -> str:
    """Backward-compatible alias for ``convert_gregorian_to_hijri_string``."""
    return convert_gregorian_to_hijri_string(value)


def _to_date(value: Any) -> date:
    """Coerce an accepted date-like value to ``date`` with a readable error."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        raise ValueError(f"Invalid date: {value!r}")
    return parsed.date()


def _convert_timestamp_to_hijri(value: pd.Timestamp) -> tuple[int, int, int] | None:
    """Convert a pandas timestamp without failing a whole DataFrame on bad data."""
    if pd.isna(value):
        return None
    try:
        hijri = Gregorian(value.year, value.month, value.day).to_hijri()
        return hijri.day, hijri.month, hijri.year
    except (ValueError, OverflowError):
        return None


_HIJRI_MONTH_NAMES = (
    "Muharram", "Safar", "Rabi al-Awwal", "Rabi al-Thani", "Jumada al-Awwal", "Jumada al-Thani",
    "Rajab", "Sha'ban", "Ramadan", "Shawwal", "Dhu al-Qi'dah", "Dhu al-Hijjah",
)
