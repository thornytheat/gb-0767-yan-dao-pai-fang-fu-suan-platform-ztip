from flask import Blueprint, render_template, request

from app.api import archive
from app.archive.certificate import issue
from app.archive.manifest import batch_key
from app.config import VERSION
from app.errors import InputError
from app.monitor.inspection import Inspection
from app.monitor.source import sample
from app.reasons import LABELS

PAGES = {'intake': '分钟原件采信', 'oxygen': '干基与参比氧折算', 'validity': '分钟有效性裁决',
         'hours': '小时汇总复算', 'reports': '报送差异对账', 'runs': '监测留档复跑', 'evidence': '监测证据签发'}
desk = Blueprint('desk', __name__)


@desk.get('/')
@desk.get('/monitor/<page>')
def show(page='home'):
    if page != 'home' and page not in PAGES:
        raise InputError('STAGE_UNKNOWN', '找不到监测工序', 404)
    name, run_id = request.args.get('sample', 'dirty'), request.args.get('run')
    history, certificate = [], None
    if run_id:
        packet = archive().require(run_id)
        results, meta = packet['results'], packet['manifest']
        if page == 'evidence':
            certificate = issue(packet)
    else:
        sources = sample(name)
        audit = Inspection(sources)
        results = audit.results()
        key, _ = batch_key(sources)
        meta = {'run_id': key, 'rule': VERSION, 'source': name, 'parameters': vars(audit.window)}
    if page == 'runs':
        history = archive().history()
    chart = [row for row in results['hours']['rows'] if row['mg_nm3'] is not None]
    ceiling = max((float(row['mg_nm3']) for row in chart), default=0)
    return render_template('base.html', page=page, pages=PAGES, name=name, run_id=run_id, history=history,
                           certificate=certificate, result=results, meta=meta, ceiling=ceiling, labels=LABELS,
                           issue_rows=[r for r in results['validity']['rows'] if r['state'] == 'missing' or r['late']])
