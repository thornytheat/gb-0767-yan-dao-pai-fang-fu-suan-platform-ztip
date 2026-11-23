from collections import Counter


def minute_counts(rows):
    return dict(Counter(row['code'] for row in rows))
