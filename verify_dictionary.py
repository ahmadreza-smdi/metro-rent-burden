"""Check the custom dictionary and its fixed ACS2024 CSV, without rewriting files."""
import csv
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
COUNTS = ['renter_units_total', 'not_computed_units', 'computable_units',
          'rent_30plus_units', 'rent_50plus_units']
PCTS = [('rent_30plus_pct', 'rent_30plus_units', 'computable_units'),
        ('rent_50plus_pct', 'rent_50plus_units', 'computable_units'),
        ('not_computed_pct_all_renters', 'not_computed_units', 'renter_units_total')]


def integer(token):
    if not isinstance(token, str) or not re.fullmatch(r'[0-9]+', token, re.ASCII):
        raise ValueError('Expected a nonnegative count in this fixed snapshot')
    return int(token)


def validate_rows(rows):
    """Validate this snapshot's all-ok rows, not a general future CSV schema."""
    ids, codes = set(), set()
    for row in rows:
        if (not row['geo_id'] or row['geo_id'] in ids or not row['metro_name']
                or not re.fullmatch(r'[0-9]{5}', row['cbsa_code'], re.ASCII)
                or row['cbsa_code'] in codes):
            raise ValueError('Empty or duplicate geography, or invalid CBSA text')
        ids.add(row['geo_id']); codes.add(row['cbsa_code'])
        if row['survey_year'] != '2024' or row['status'] != 'ok':
            raise ValueError('Wrong vintage or status for this fixed snapshot')
        estimates = {i: integer(row[f'B25070_E{i:03}']) for i in range(1, 12)}
        for i in range(1, 12):
            integer(row[f'B25070_M{i:03}'])
        total, unknown = estimates[1], estimates[11]
        denominator = total - unknown
        if sum(estimates[i] for i in range(2, 12)) != total or denominator <= 0:
            raise ValueError('Nonadditive or zero-denominator row in all-ok snapshot')
        expected = [total, unknown, denominator,
                    sum(estimates[i] for i in range(7, 11)), estimates[10]]
        for name, value in zip(COUNTS, expected):
            if integer(row[name]) != value:
                raise ValueError('Derived count mismatch: ' + name)
        if not 0 <= expected[4] <= expected[3] <= denominator:
            raise ValueError('Threshold nesting mismatch')
        for name, numerator, divisor in PCTS:
            try:
                value = Decimal(row[name])
                exact = Decimal(100) * Decimal(row[numerator]) / Decimal(row[divisor])
            except (InvalidOperation, ZeroDivisionError):
                raise ValueError('Unavailable or invalid percentage in all-ok snapshot')
            if not value.is_finite() or not 0 <= value <= 100 or abs(value - exact) > Decimal('0.0000005'):
                raise ValueError('Derived percentage mismatch: ' + name)


def verify(root=ROOT):
    dictionary = json.loads((root / 'data-dictionary.json').read_text(encoding='utf-8'))
    if dictionary['format_version'] != 1:
        raise ValueError('Unsupported custom dictionary version')
    for spec in [dictionary['dataset'], dictionary['source_metadata']]:
        if hashlib.sha256((root / spec['file']).read_bytes()).hexdigest() != spec['sha256']:
            raise ValueError('Dictionary snapshot hash mismatch: ' + spec['file'])
    metadata = json.loads((root / dictionary['source_metadata']['file']).read_text(encoding='utf-8'))['variables']
    with (root / dictionary['dataset']['file']).open(newline='', encoding='utf-8') as handle:
        reader = csv.DictReader(handle)
        fields = dictionary['fields']
        names = [f['name'] for f in fields]
        if names != reader.fieldnames or len(names) != 35 or len(set(names)) != 35:
            raise ValueError('Dictionary/header order, width or uniqueness mismatch')
        for field in fields:
            if not field['meaning'] or not field['unit'] or not field['kind']:
                raise ValueError('Incomplete dictionary field')
            match = re.fullmatch(r'B25070_([EM])([0-9]{3})', field['name'])
            if match:
                role, number = match.groups()
                source = f'B25070_{number}{role}'
                partner = f'B25070_{"M" if role == "E" else "E"}{number}'
                if (field['source_variable'] != source or field['source_label'] != metadata[source]['label']
                        or field['paired_field'] != partner or partner not in names
                        or field['source_role'] != ('estimate' if role == 'E' else 'margin_of_error')):
                    raise ValueError('Source-label or pair mismatch: ' + field['name'])
        for name, _, denominator in PCTS:
            field = fields[names.index(name)]
            if field['unit'] != 'percent (0–100)' or field['denominator'] != denominator:
                raise ValueError('Percentage unit or denominator mismatch: ' + name)
        rows = list(reader)
    if len(rows) != 386 or dictionary['dataset']['rows'] != 386 or dictionary['dataset']['columns'] != 35:
        raise ValueError('Wrong snapshot row/column count')
    validate_rows(rows)
    return {'rows': len(rows), 'columns': len(fields), 'source_estimate_moe_pairs': 11,
            'derived_percentage_checks': len(rows) * 3, 'result': 'PASS'}


if __name__ == '__main__':
    print(json.dumps(verify(), sort_keys=True))
