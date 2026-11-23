from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

EMPTY = frozenset({'', '-', 'N/A', 'NULL', '未知'})
CENT = Decimal('0.01')


def number(raw):
    if raw is None or str(raw).strip().upper() in EMPTY:
        raise ValueError('MISSING_NUMBER')
    try:
        value = Decimal(raw.strip())
    except (AttributeError, InvalidOperation):
        raise ValueError('UNSAFE_NUMBER') from None
    if not value.is_finite() or abs(value) > 1_000_000 or value.as_tuple().exponent < -8:
        raise ValueError('UNSAFE_NUMBER')
    return value


def display(value):
    return format(value.quantize(CENT, rounding=ROUND_HALF_UP), 'f')
