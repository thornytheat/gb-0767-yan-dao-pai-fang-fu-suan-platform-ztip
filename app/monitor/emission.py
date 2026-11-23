from decimal import Decimal, localcontext

from app.monitor.clock import HOUR, MINUTE, local
from app.numbers import display3

MG_PER_KG = Decimal(1_000_000)


def account(rows, flows, window):
    """小时排放量判定：缺测流量不补零，已核算部分超限即判超限。"""
    limit_mg = window.emission_limit * MG_PER_KG
    limit_kg = display3(window.emission_limit)
    result = []
    for index in range(0, len(rows), 60):
        hour = window.start + (index // 60) * HOUR
        exempt = pending = 0
        with localcontext() as ctx:
            ctx.prec = 40
            total = Decimal(0)
            for offset, item in enumerate(rows[index:index + 60]):
                if item['state'] == 'exempt':
                    exempt += 1
                    continue
                flow = flows.get(window.start + (index + offset) * MINUTE)
                if item['state'] == 'valid' and flow is not None:
                    total += item['dry'] * flow['nm3_min']
                else:
                    pending += 1
            kg = display3(total / MG_PER_KG)
        accounted = 60 - exempt - pending
        if exempt == 60:
            code = 'EXEMPT'
        elif total > limit_mg:
            code = 'EXCEEDED'
        elif pending:
            code = 'PENDING'
        else:
            code = 'COMPLIANT'
        result.append({'hour': hour.isoformat(), 'local': local(hour), 'code': code,
                       'accounted': accounted, 'pending': pending, 'exempt': exempt,
                       'kg': kg, 'limit_kg': limit_kg,
                       'basis': basis(code, accounted, pending, kg, limit_kg)})
    return result


def basis(code, accounted, pending, kg, limit_kg):
    if code == 'EXEMPT':
        return '整小时工况免计，不核算排放量'
    if code == 'EXCEEDED':
        if not pending:
            return f'{accounted}分钟全部核算合计{kg} kg，超限值{limit_kg} kg/h'
        return (f'已核算{accounted}分钟合计{kg} kg，已超限值{limit_kg} kg/h；'
                f'其余{pending}分钟缺数且分钟排放非负，合计只增不减，判定不待补齐')
    if code == 'PENDING':
        return (f'已核算{accounted}分钟合计{kg} kg暂未超限，其余{pending}分钟缺数；'
                f'缺测流量不补零，补齐前不作达标结论')
    return f'{accounted}分钟全部核算合计{kg} kg，未超限值{limit_kg} kg/h'
