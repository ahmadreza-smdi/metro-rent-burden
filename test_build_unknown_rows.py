"""Synthetic complete-file builds preserve unknowns regardless of first row."""
import csv
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent
DERIVED = ['renter_units_total', 'not_computed_units', 'computable_units',
           'rent_30plus_units', 'rent_50plus_units', 'rent_30plus_pct',
           'rent_50plus_pct', 'not_computed_pct_all_renters']


class UnknownRows(unittest.TestCase):
    def build(self, unknown):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); (root / 'raw').mkdir(); shutil.copyfile(ROOT / 'build.py', root / 'build.py')
            table = []; geographies = []
            for index, unavailable in enumerate(unknown):
                code = str(99000 + index); geo_id = '310M600US' + code
                row = {'GEO_ID': geo_id}
                values = [100, 10, 10, 10, 5, 5, 10, 10, 10, 10, 20]
                for i, value in enumerate(values, 1):
                    row[f'B25070_E{i:03}'] = '-666666666' if unavailable and i == 10 else str(value)
                    row[f'B25070_M{i:03}'] = '1'
                table.append(row)
                geographies.append({'GEO_ID': geo_id, 'CBSA': code, 'NAME': f'Fictional {index}, ZZ Metro Area', 'SUMLEVEL': '310', 'COMPONENT': '00'})
            receipt = {'survey_year': 2024, 'fictional_test_fixture': True, 'sources': []}
            for name, rows in [('2024-b25070.dat', table), ('2024-geographies.txt', geographies)]:
                out = io.StringIO(newline=''); writer = csv.DictWriter(out, fieldnames=list(rows[0]), delimiter='|')
                writer.writeheader(); writer.writerows(rows); raw = out.getvalue().encode()
                (root / 'raw' / name).write_bytes(raw)
                receipt['sources'].append({'file': 'raw/' + name, 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)})
            (root / 'source-2024.json').write_text(json.dumps(receipt))
            result = subprocess.run([sys.executable, '-B', str(root / 'build.py')], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            reader = csv.DictReader(io.StringIO((root / 'metro-rent-burden-2024.csv').read_text()))
            fields = reader.fieldnames; rows = list(reader)
            summary = json.loads((root / 'summary-2024.json').read_text())
            return fields, rows, summary

    def test_unavailable_first_row_does_not_remove_output_columns(self):
        fields, rows, summary = self.build([True, False])
        self.assertEqual(len(fields), 35)
        self.assertEqual(rows[0]['status'], 'unavailable source estimate')
        self.assertTrue(all(rows[0][field] == '' for field in DERIVED))
        self.assertEqual(rows[0]['B25070_E010'], '-666666666')
        self.assertEqual(float(rows[1]['rent_30plus_pct']), 50)
        self.assertIsNone(summary['not_computed_total_selected'])

    def test_unknown_later_row_does_not_become_partial_known_total(self):
        _, rows, summary = self.build([False, True])
        self.assertEqual(rows[1]['computable_units'], '')
        self.assertIsNone(summary['not_computed_total_selected'])

    def test_all_unavailable_retains_complete_schema_and_unknown_total(self):
        fields, rows, summary = self.build([True, True])
        self.assertEqual(len(fields), 35)
        self.assertEqual(summary['unavailable_rows'], 2)
        self.assertIsNone(summary['not_computed_total_selected'])
        self.assertEqual(summary['chart_rows'], [])

    def test_all_known_keeps_actual_known_sum(self):
        _, rows, summary = self.build([False, False])
        self.assertEqual(summary['not_computed_total_selected'], 40)
        self.assertEqual(len(rows), 2)


if __name__ == '__main__':
    unittest.main()
