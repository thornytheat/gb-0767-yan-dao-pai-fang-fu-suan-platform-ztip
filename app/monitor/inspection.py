from collections import Counter
from functools import cached_property

from app.monitor.counts import minute_counts
from app.monitor.emission import account
from app.monitor.flow import choose_flows
from app.monitor.hours import aggregate
from app.monitor.modes import mode_windows
from app.monitor.oxygen import correct
from app.monitor.reconcile import compare
from app.monitor.revision import choose
from app.monitor.source import intake
from app.monitor.validity import minute_evidence
from app.numbers import display, display3

STAGES = ('intake', 'oxygen', 'validity', 'hours', 'reports')


class Inspection:
    def __init__(self, files):
        self.window, self.ledgers = intake(files)

    @cached_property
    def intake(self):
        return {'files': [stats for _, stats in self.ledgers.values()]}

    @cached_property
    def corrected(self):
        selected, conflicts, isolated = choose(self.ledgers['minutes'][0], self.window)
        for when, reading in selected.items():
            evidence = reading | {'utc': when.isoformat()}
            try:
                dry, adjusted = correct(reading['fields'], self.window.reference)
                evidence.update(dry_mg_nm3=display(dry), reference_mg_nm3=display(adjusted),
                                dry_raw=dry, reference_raw=adjusted, code='VALID')
            except ValueError as error:
                evidence.update(dry_mg_nm3=None, reference_mg_nm3=None, code=str(error))
                isolated.append(evidence)
            selected[when] = evidence
        return selected, conflicts, isolated

    @cached_property
    def oxygen(self):
        selected, _, isolated = self.corrected
        return {'reference_pct': str(self.window.reference), 'rows': list(selected.values()), 'isolated': isolated}

    @cached_property
    def validity(self):
        selected, conflicts, _ = self.corrected
        intervals, isolated = mode_windows(self.ledgers['modes'][0], self.window)
        rows = list(minute_evidence(self.window, selected, conflicts, intervals))
        return {'rows': rows, 'isolated_modes': isolated, 'reason_counts': minute_counts(rows)}

    @cached_property
    def flow_selection(self):
        return choose_flows(self.ledgers['flows'][0], self.window)

    @cached_property
    def hours(self):
        rows = aggregate(self.validity['rows'], self.window)
        flows, flows_isolated = self.flow_selection
        emissions = account(self.validity['rows'], flows, self.window)
        rows = [row | {'emission': emission} for row, emission in zip(rows, emissions, strict=True)]
        verdicts = Counter(emission['code'] for emission in emissions)
        return {'rows': rows, 'flows_isolated': flows_isolated,
                'totals': {key: sum(row[key] for row in rows) for key in
                           ('scheduled', 'valid', 'exempt', 'missing', 'late')},
                'emission': {'limit_kg': display3(self.window.emission_limit),
                             'exceeded': verdicts['EXCEEDED'], 'pending': verdicts['PENDING'],
                             'compliant': verdicts['COMPLIANT'], 'exempt': verdicts['EXEMPT']}}

    @cached_property
    def reports(self):
        rows, isolated = compare(self.hours['rows'], self.ledgers['reports'][0], self.window)
        return {'rows': rows, 'isolated': isolated, 'deviations': sum(row['code'] == 'DEVIATION' for row in rows)}

    def results(self):
        return {stage: getattr(self, stage) for stage in STAGES}
