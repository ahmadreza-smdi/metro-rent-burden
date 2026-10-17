#!/usr/bin/env python3
"""Rebuild one reading-aid figure from the unchanged ACS 2024 snapshot."""
import csv
import hashlib
import html
import json
from pathlib import Path
import re

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from build import measures, verify_snapshot

ROOT = Path(__file__).resolve().parent
CSV_SHA256 = '3f4f802c00efda62f2166cf0f6cfef99d0046becda55ba35c9563c232d84821f'


def main():
    verify_snapshot(ROOT, 2024)
    source = ROOT / 'metro-rent-burden-2024.csv'
    if hashlib.sha256(source.read_bytes()).hexdigest() != CSV_SHA256:
        raise ValueError('The fixed 2024 CSV changed; reconcile this reading aid')
    with source.open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    selected = min(rows, key=lambda row: int(row['cbsa_code']))
    with (ROOT / 'raw/2024-b25070.dat').open(newline='', encoding='utf-8-sig') as stream:
        raw = next(row for row in csv.DictReader(stream, delimiter='|')
                   if row['GEO_ID'] == selected['geo_id'])
    for key, value in raw.items():
        if key != 'GEO_ID' and selected[key] != value:
            raise ValueError('CSV estimate/MOE differs from raw source: ' + key)
    values = measures(raw)
    if values['status'] != 'ok':
        raise ValueError('Selected row has no computable denominator')
    denominator = values['computable_units']
    counts = [sum(int(raw[f'B25070_E{i:03}']) for i in range(2, 7)),
              sum(int(raw[f'B25070_E{i:03}']) for i in range(7, 10)),
              int(raw['B25070_E010'])]
    assert sum(counts) == denominator
    assert counts[1] + counts[2] == values['rent_30plus_units']
    assert counts[2] == values['rent_50plus_units']
    percentages = [100 * count / denominator for count in counts]
    nested = 100 * (counts[1] + counts[2]) / denominator
    labels = ['Below 30%', '30.0–49.9%', '50% or more']
    alt = (f"ACS 2024 point estimates for {selected['metro_name']}. "
           f"The percentage denominator is {denominator:,} computable renter-occupied units. "
           + '; '.join(f'{label}: {count:,} estimated units, {share:.1f}%'
                       for label, count, share in zip(labels, counts, percentages))
           + f". The last two disjoint groups together are the 30%+ group: "
             f"{counts[1] + counts[2]:,} estimated units, {nested:.1f}%. "
             f"The 50%+ group is already included, so do not add the two thresholds. "
             f"{values['not_computed_units']:,} not-computed units are excluded from that denominator; "
             f"all renter-occupied units total {values['renter_units_total']:,}. "
             'Derived percentage margins of error are not calculated. This is not an investment ranking.')

    plt.rcParams.update({'font.family': 'DejaVu Sans', 'svg.fonttype': 'none',
                         'svg.hashsalt': 'rent-burden-threshold-2024'})
    background, ink, secondary = '#f5faf8', '#203c42', '#365f79'
    colors = ['#dceaf0', '#8fcdbb', '#365f79']
    fig = plt.figure(figsize=(9, 12), dpi=140, facecolor=background)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.axis('off')
    def text(x, y, value, size=22, **kwargs):
        return ax.text(x, y, value, fontsize=size, color=ink, va='top', **kwargs)
    text(.06, .965, 'One group is inside\nthe other.', 32, weight='bold')
    text(.06, .858, selected['metro_name'].removesuffix(' Metro Area'), 25)
    text(.06, .817, 'ACS 2024 · Gross rent / household income', 21)
    text(.06, .762, 'Share of computable renter-occupied units', 21)

    left, width, y, height = .06, .88, .655, .065
    offset = 0
    for index, (share, color) in enumerate(zip(percentages, colors)):
        segment = width * share / 100
        ax.add_patch(Rectangle((left + offset, y), segment, height,
                               facecolor=color, edgecolor='none'))
        ax.text(left + offset + segment / 2, y + height / 2,
                f'{share:.1f}%', ha='center', va='center', fontsize=24,
                color='white' if index == 2 else ink)
        offset += segment
    start = left + width * percentages[0] / 100
    end = left + width
    ax.plot([start, start, end, end], [.642, .627, .627, .642], color=secondary, lw=1.5)
    ax.text((start + end) / 2, .61, f'30%+ together: {nested:.1f}%',
            ha='center', va='top', fontsize=22, color=ink)
    text(.06, .548, 'Income share', 19)
    text(.94, .548, 'Estimated units', 19, ha='right')
    for index, (label, count, color) in enumerate(zip(labels, counts, colors)):
        row_y = .505 - index * .052
        ax.add_patch(Rectangle((.06, row_y - .023), .027, .022,
                               facecolor=color, edgecolor='none'))
        text(.105, row_y, label, 24)
        text(.94, row_y, f'{count:,}', 24, ha='right')
    text(.06, .335, f'{denominator:,} computable units', 25)
    text(.06, .287, f"{values['not_computed_units']:,} not-computed units excluded", 21)
    text(.06, .247, f"All renter-occupied units: {values['renter_units_total']:,}", 21)
    text(.06, .172, 'Survey point estimates. Derived percentage\nmargins of error are not calculated.', 19)
    text(.06, .091, 'U.S. Census Bureau · ACS 1-year B25070', 19)
    text(.06, .047, 'Ahmadreza Samadi · a-samadi.com', 19)

    output = ROOT / 'docs'
    output.mkdir(exist_ok=True)
    fig.savefig(output / 'nested-thresholds-2024.png', facecolor=background)
    svg_path = output / 'nested-thresholds-2024.svg'
    fig.savefig(svg_path, facecolor=background, metadata={'Date': None})
    plt.close(fig)
    svg = svg_path.read_text()
    match = re.search(r'<svg\b[^>]*>', svg)
    assert match
    opening = match.group(0)[:-1] + ' role="img" aria-labelledby="chart-title chart-description">'
    opening += ('<title id="chart-title">Nested rent-burden thresholds, ACS 2024</title>'
                '<desc id="chart-description">' + html.escape(alt) + '</desc>')
    svg_path.write_text(svg[:match.start()] + opening + svg[match.end():])
    (output / 'nested-thresholds-alt.txt').write_text(alt + '\n')
    receipt = {'survey_year': 2024, 'selection': 'Lowest numeric CBSA code in the fixed stored CSV; not selected by burden',
               'source_csv_sha256': CSV_SHA256, 'source_geo_id': selected['geo_id'],
               'source_metro': selected['metro_name'], 'source_table': 'ACS 1-year B25070',
               'source_url': 'https://data.census.gov/table/ACSDT1Y2024.B25070',
               'computable_units': denominator, 'groups': [dict(label=label, estimated_units=count, share_pct=share)
               for label, count, share in zip(labels, counts, percentages)],
               'at_least_30_pct': nested, 'not_computed_units': values['not_computed_units'],
               'all_renter_occupied_units': values['renter_units_total'],
               'derived_percentage_MOEs': 'Not calculated', 'matplotlib_version': matplotlib.__version__}
    (output / 'nested-thresholds-source.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'metro': selected['metro_name'], 'groups': counts,
                      'computable_units': denominator, 'at_least_30_pct': nested}))


if __name__ == '__main__':
    main()
