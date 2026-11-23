from datetime import UTC, datetime, timedelta, timezone

MINUTE = timedelta(minutes=1)
HOUR = timedelta(hours=1)
LOCAL = timezone(timedelta(hours=8))


def instant(text):
    try:
        value = datetime.fromisoformat(text.replace('Z', '+00:00'))
        if value.tzinfo is None or not 2000 <= value.year <= 2099:
            raise ValueError
        return value.astimezone(UTC)
    except (AttributeError, ValueError, OverflowError):
        raise ValueError('BAD_TIME') from None


def minute(text):
    value = instant(text)
    if value.second or value.microsecond:
        raise ValueError('BAD_TIME')
    return value


def local(value):
    return value.astimezone(LOCAL).strftime('%m-%d %H:%M')
