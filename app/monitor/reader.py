import csv
from io import StringIO

from app.errors import InputError
from app.monitor.schema import HEADERS


def read_csv(text, source):
    reader = csv.reader(StringIO(text.removeprefix('\ufeff'), newline=''), strict=True)
    rows, rejected = [], []
    headers = HEADERS[source]
    repeats, physical_rows = 0, 0
    try:
        header = next(reader, None)
        if header is None:
            raise InputError('EMPTY_FILE', f'{source} 缺 CSV 表头')
        if len(header) != len(headers) or set(header) != set(headers):
            raise InputError('BAD_HEADER', f'{source} 表头与定义不符')
        while True:
            line = reader.line_num + 1
            values = next(reader, None)
            if values is None:
                break
            physical_rows += 1
            evidence = {'source': source, 'line': line, 'raw': values}
            if values == header:
                repeats += 1
            elif not any(value.strip() for value in values):
                rejected.append(evidence | {'code': 'BLANK'})
            elif len(values) != len(header):
                rejected.append(evidence | {'code': 'COLUMN_COUNT'})
            else:
                rows.append(evidence | {'fields': dict(zip(header, values, strict=True))})
    except csv.Error:
        raise InputError('MALFORMED_CSV', f'{source} 第 {reader.line_num} 行 CSV 引号异常') from None
    state = 'rows' if rows else 'header_only' if physical_rows == 0 else 'no_usable_rows'
    return rows, {'source': source, 'input': physical_rows, 'parsed': len(rows), 'headers': repeats,
                  'isolated': len(rejected), 'state': state, 'rejected': rejected}
