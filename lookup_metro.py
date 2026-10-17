"""Read exact rows from the fixed ACS 2024 companion CSV; no network or writes."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re

from verify_dictionary import verify

ROOT = Path(__file__).resolve().parent


def lookup(*, search=None, codes=None, root=ROOT):
    """Search names or select explicit codes; never infer a geographic match."""
    if (search is None) == (codes is None):
        raise ValueError('Choose either a name search or explicit CBSA codes')
    if search is not None:
        if not isinstance(search, str) or not search.strip():
            raise ValueError('Name search must contain text')
        search = search.strip().casefold()
    else:
        if (not isinstance(codes, (list, tuple)) or not codes
                or any(not isinstance(c, str) or not re.fullmatch(r'[0-9]{5}', c, re.ASCII) for c in codes)):
            raise ValueError('Each CBSA code must be exactly five ASCII digits')
        if len(set(codes)) != len(codes):
            raise ValueError('Duplicate CBSA codes are not accepted')
    # Reuse the existing fixed-snapshot validator, including all estimate/MOE
    # pairs, denominators, vintage and source-metadata hashes.
    verify(root)
    dictionary = json.loads((root / 'data-dictionary.json').read_text(encoding='utf-8'))
    snapshot = dictionary['dataset']
    raw = (root / snapshot['file']).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != snapshot['sha256']:
        raise ValueError('CSV changed after verification')
    rows = list(csv.DictReader(io.StringIO(raw.decode('utf-8'), newline='')))
    if codes is not None:
        missing = sorted(set(codes) - {row['cbsa_code'] for row in rows})
        if missing:
            raise ValueError('Code absent from this fixed snapshot: ' + ', '.join(missing))
        selected = [row for row in rows if row['cbsa_code'] in codes]
    else:
        selected = [row for row in rows if search in row['metro_name'].casefold()]
    return {
        'format': 'metro-rent-burden-lookup-v1',
        'author': dictionary['author'],
        'source': {'agency': 'U.S. Census Bureau', 'table': 'B25070',
                   'product': 'ACS 1-year', 'survey_year': 2024,
                   'url': 'https://data.census.gov/table/ACSDT1Y2024.B25070'},
        'snapshot': {'file': snapshot['file'], 'sha256': digest,
                     'total_rows': snapshot['rows'], 'columns': snapshot['columns']},
        'selection': {'name_contains': search, 'requested_codes': codes,
                      'matched_rows': len(selected), 'order': 'Original CSV order; not a ranking'},
        'interpretation': {
            'value_encoding': 'All 35 CSV values are preserved as strings, including code leading zeros and blank cells. Percentages use the 0–100 scale.',
            'burden_denominator': 'computable_units = renter_units_total - not_computed_units',
            'not_computed_denominator': 'not_computed_pct_all_renters uses renter_units_total',
            'thresholds': 'At-least-50% units are included in at-least-30% units; do not add the shares.',
            'uncertainty': '11 published estimate/MOE pairs retained per row. Derived percentage MOEs and statistical significance are not calculated.',
            'scope': 'Fixed selected whole metros in 50 states/DC. No current asking rents, household microdata, geographic match certification, investment ranking or new observations.',
            'missing_selection': 'Zero name matches means absent from this search, not zero burden. An unknown explicit code is an error.'},
        'rows': selected}


def format_text(result):
    """Read selected stored values without recalculating or rounding them."""
    def value(row, key, suffix=''):
        raw = row[key]
        return 'Unavailable (blank in stored CSV)' if raw == '' else raw + suffix

    lines = [
        'Metro rent burden — ACS 2024',
        f"By {result['author']['name']} — {result['author']['url']}",
        f"Source: {result['source']['url']}",
        f"Snapshot SHA-256: {result['snapshot']['sha256']}",
        f"Matching metros: {result['selection']['matched_rows']}",
        'Original CSV order; not a ranking.',
    ]
    if not result['rows']:
        lines.append('No matching row in this search; this does not mean zero burden.')
    for row in result['rows']:
        lines.extend([
            '', f"{row['metro_name']} (CBSA {row['cbsa_code']})",
            f"Survey year: {row['survey_year']}; status: {row['status']}",
            'Total renter-occupied housing units: ' + value(row, 'renter_units_total'),
            'Not-computed ratio: ' + value(row, 'not_computed_units') + ' units',
            'Computable units (burden-share denominator): ' + value(row, 'computable_units'),
            'At least 30% of income in gross rent: ' + value(row, 'rent_30plus_pct', '%')
                + ' (' + value(row, 'rent_30plus_units') + ' units)',
            'At least 50% of income in gross rent: ' + value(row, 'rent_50plus_pct', '%')
                + ' (' + value(row, 'rent_50plus_units') + ' units)',
            'Not-computed share of ALL renter-occupied units: ' + value(row, 'not_computed_pct_all_renters', '%'),
        ])
    lines.extend([
        '', 'Read before comparing:',
        'The 50% group is inside the 30% group; do not add their shares.',
        'Derived percentage margins of error and statistical significance are not calculated.',
        'Blank values are unavailable, not zero. Stored precision is retained without rounding.',
        'This fixed 2024 snapshot is not current asking rents or an investment ranking.',
        'For all 35 original fields and all 11 source estimate/MOE pairs, use --format json.',
    ])
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--search', help='Case-insensitive substring of the published metro name')
    group.add_argument('--code', dest='codes', action='append', help='Exact five-digit CBSA code; repeat for multiple rows')
    parser.add_argument('--format', dest='output_format', choices=('json', 'text'), default='json',
                        help='JSON preserves all fields (default); text summarizes stored values and limits')
    args = parser.parse_args()
    try:
        result = lookup(search=args.search, codes=args.codes)
    except (ValueError, KeyError, OSError) as exc:
        parser.error(str(exc))
    print(format_text(result) if args.output_format == 'text' else json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
