"""Behavioral checks against the unchanged released CSV and corrupted copies."""
import csv
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from lookup_metro import lookup, ROOT


class LookupTests(unittest.TestCase):
    def setUp(self):
        with (ROOT / 'metro-rent-burden-2024.csv').open(newline='', encoding='utf-8') as f:
            self.rows = list(csv.DictReader(f))

    def test_selection_preserves_every_field_and_source_order(self):
        codes = [self.rows[-1]['cbsa_code'], self.rows[0]['cbsa_code']]
        result = lookup(codes=codes)
        self.assertEqual(result['rows'], [self.rows[0], self.rows[-1]])
        self.assertEqual(len(result['rows'][0]), 35)
        self.assertEqual(result['source']['survey_year'], 2024)
        self.assertEqual(result['selection']['matched_rows'], 2)
        for row in result['rows']:
            self.assertTrue(all(isinstance(value, str) for value in row.values()))
            self.assertTrue(all(f'B25070_M{i:03}' in row for i in range(1, 12)))

    def test_case_insensitive_search_and_empty_match(self):
        token = self.rows[0]['metro_name'].split(',')[0]
        expected = [r for r in self.rows if token.casefold() in r['metro_name'].casefold()]
        self.assertEqual(lookup(search='  ' + token.upper() + '  ')['rows'], expected)
        empty = lookup(search='NO_SUCH_METRO_123456')
        self.assertEqual(empty['rows'], [])
        self.assertEqual(empty['selection']['matched_rows'], 0)
        self.assertIn('not zero burden', empty['interpretation']['missing_selection'])

    def test_unknown_or_ambiguous_inputs_fail_without_partial_output(self):
        known = self.rows[0]['cbsa_code']
        for kwargs in [{}, {'search':' '}, {'codes':[]}, {'codes':[known, known]},
                       {'codes':[known, '00000']}, {'codes':['１２３４５']},
                       {'codes':[12345]}, {'search':'a', 'codes':[known]}]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                lookup(**kwargs)

    def test_changed_csv_or_metadata_is_refused(self):
        dictionary = json.loads((ROOT / 'data-dictionary.json').read_text())
        for changed in [dictionary['dataset']['file'], dictionary['source_metadata']['file']]:
            with self.subTest(changed=changed), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                for name in ['data-dictionary.json', dictionary['dataset']['file'], dictionary['source_metadata']['file']]:
                    target = root / name; target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(ROOT / name, target)
                with (root / changed).open('ab') as f:
                    f.write(b'\n')
                with self.assertRaises(ValueError):
                    lookup(search='New', root=root)

    def test_cli_works_outside_repo_and_unknown_code_has_no_json(self):
        script = str(ROOT / 'lookup_metro.py')
        known = self.rows[0]['cbsa_code']
        with tempfile.TemporaryDirectory() as tmp:
            good = subprocess.run([sys.executable, '-B', script, '--code', known], cwd=tmp, capture_output=True, text=True)
            self.assertEqual(good.returncode, 0)
            self.assertEqual(json.loads(good.stdout)['rows'], [self.rows[0]])
            bad = subprocess.run([sys.executable, '-B', script, '--code', known, '--code', '00000'], cwd=tmp, capture_output=True, text=True)
            self.assertEqual(bad.returncode, 2)
            self.assertEqual(bad.stdout, '')


if __name__ == '__main__':
    unittest.main()
