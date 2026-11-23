from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.errors import InputError
from app.monitor.clock import HOUR, minute
from app.numbers import number

HEADERS = {
    'minutes': 'stack,timestamp,value,unit,basis,moisture,oxygen,status,revision,received'.split(','),
    'modes': 'stack,start,end,mode'.split(','),
    'reports': 'stack,hour,value,ticket'.split(','),
}


@dataclass(frozen=True)
class Window:
    stack: str
    start: datetime
    end: datetime
    cutoff: datetime
    reference: Decimal
    threshold: int
    tolerance: Decimal

    @classmethod
    def parse(cls, raw):
        try:
            start, end, cutoff = (minute(raw[key]) for key in ('start', 'end', 'cutoff'))
            stack, threshold = raw['stack'], raw['threshold']
            reference, tolerance = (number(raw[key]) for key in ('reference', 'tolerance'))
            if (not isinstance(stack, str) or not stack.strip() or len(stack) > 40
                    or start.minute or end.minute or not HOUR <= end - start <= 24 * HOUR
                    or cutoff < end or type(threshold) is not int or not 1 <= threshold <= 60
                    or not 0 <= reference <= 20 or tolerance < 0):
                raise ValueError
        except (KeyError, TypeError, ValueError):
            raise InputError('BAD_WINDOW', '监测时窗、截止或规则参数无效') from None
        return cls(stack, start, end, cutoff, reference, threshold, tolerance)
