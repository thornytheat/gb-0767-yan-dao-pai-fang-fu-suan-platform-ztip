from pathlib import Path

SAMPLES = Path(__file__).resolve().parent.parent / 'sample_data'
VERSION = 'CEMS-1.1'
SOURCE_LIMIT = 400_000
FILES = ('window', 'minutes', 'modes', 'reports', 'flows')
