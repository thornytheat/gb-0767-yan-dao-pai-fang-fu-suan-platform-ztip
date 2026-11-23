from decimal import Decimal, localcontext

from app.numbers import number

FACTORS = {'mg/Nm3': Decimal(1), 'g/Nm3': Decimal(1000), 'ug/Nm3': Decimal('0.001'),
           'µg/Nm3': Decimal('0.001')}
AIR_O2 = Decimal(21)


def correct(fields, reference):
    if fields['unit'] not in FACTORS:
        raise ValueError('BAD_UNIT')
    basis = fields['basis']
    if basis not in {'wet', 'dry'}:
        raise ValueError('BAD_BASIS')
    oxygen = number(fields['oxygen'])
    if not 0 <= oxygen <= 20:
        raise ValueError('BAD_OXYGEN')
    concentration = number(fields['value'])
    if concentration < 0:
        raise ValueError('NEGATIVE')
    moisture = number(fields['moisture']) if basis == 'wet' else Decimal(0)
    if not 0 <= moisture < 100:
        raise ValueError('BAD_MOISTURE')
    with localcontext() as ctx:
        ctx.prec = 40
        dry = concentration * FACTORS[fields['unit']] * 100 / (100 - moisture)
        return dry, dry * (AIR_O2 - reference) / (AIR_O2 - oxygen)
