"""Check the saved XLSX against the versioned CSV, using Python's standard library.

This checks stored data, formula caches and structure. It does not run Excel.
"""
from pathlib import Path
import csv
import json
import xml.etree.ElementTree as ET
import zipfile

NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
ROOT = Path(__file__).resolve().parent


def read_sheet(archive, name, strings):
    tree = ET.fromstring(archive.read(name))
    cells = {}
    for cell in tree.findall('.//m:sheetData/m:row/m:c', NS):
        value = cell.find('m:v', NS)
        kind = cell.get('t')
        if kind == 's':
            value = strings[int(value.text)]
        elif kind == 'inlineStr':
            value = ''.join(cell.itertext())
        elif value is None:
            value = None
        elif kind in ('str', 'e'):
            value = value.text
        else:
            value = float(value.text)
        if kind == 'e':
            raise ValueError('Error cell: ' + cell.attrib['r'])
        cells[cell.attrib['r']] = (value, cell.findtext('m:f', namespaces=NS))
    return tree, cells


def column(index):
    name = ''
    while index:
        index, mod = divmod(index - 1, 26)
        name = chr(65 + mod) + name
    return name


def verify():
    with (ROOT / 'metro-rent-burden-2024.csv').open(newline='') as stream:
        reader = csv.DictReader(stream)
        headers = reader.fieldnames
        rows = list(reader)
    assert len(rows) == 386 and len(headers) == 35
    with zipfile.ZipFile(ROOT / 'Metro-Rent-Burden-2024.xlsx') as archive:
        shared = ET.fromstring(archive.read('xl/sharedStrings.xml'))
        strings = [''.join(item.itertext()) for item in shared]
        workbook = ET.fromstring(archive.read('xl/workbook.xml'))
        assert [s.get('name') for s in workbook.find('m:sheets', NS)] == ['Metros', 'Source']
        metro_tree, metros = read_sheet(archive, 'xl/worksheets/sheet1.xml', strings)
        source_tree, source = read_sheet(archive, 'xl/worksheets/sheet2.xml', strings)
        for c, header in enumerate(headers, 1):
            assert source[f'{column(c)}16'][0] == header
        for i, row in enumerate(rows):
            for c, key in enumerate(headers, 1):
                expected = row[key] if key in ('geo_id', 'cbsa_code', 'metro_name', 'status') else float(row[key])
                assert source[f'{column(c)}{i + 17}'][0] == expected, (i, key)
            expected = [row['metro_name'], row['cbsa_code'], 2024]
            expected += [int(row[k]) for k in ('renter_units_total', 'not_computed_units', 'computable_units', 'rent_30plus_units', 'rent_50plus_units')]
            expected += [float(row[k]) / 100 for k in ('rent_30plus_pct', 'rent_50plus_pct', 'not_computed_pct_all_renters')]
            for c, expected_value in enumerate(expected, 1):
                value, formula = metros[f'{column(c)}{i + 10}']
                assert formula, (i, c, 'Missing formula')
                assert value == expected_value if c < 9 else abs(value - expected_value) <= 5.1e-9, (i, c)
        for tree, cell in [(metro_tree, 'A10'), (source_tree, 'A17')]:
            assert tree.find('.//m:pane', NS).get('topLeftCell') == cell
        tables = [ET.fromstring(archive.read(name)) for name in archive.namelist() if name.startswith('xl/tables/') and name.endswith('.xml')]
        assert sorted(t.get('ref') for t in tables) == ['A16:AI402', 'A9:K395']
        assert all(t.find('m:autoFilter', NS) is not None for t in tables)
    return {'rows_checked': len(rows), 'source_fields': len(headers), 'cached_outputs_match_csv': True, 'native_excel_execution': False}


if __name__ == '__main__':
    print(json.dumps(verify()))
