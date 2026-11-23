from pathlib import Path

SAMPLES = Path(__file__).resolve().parent.parent / 'sample_data'
VERSION = 'CEMS-1.0'
SOURCE_LIMIT = 400_000
FILES = ('window', 'minutes', 'modes', 'reports')
