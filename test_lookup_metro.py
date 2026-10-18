"""Behavioral checks against the unchanged released CSV and corrupted copies."""
import csv
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

from lookup_metro import lookup, format_text, ROOT


class LookupTests(unittest.TestCase):
    def setUp(self):
        with (ROOT / 'metro-rent-burden-2024.csv').open(newline='', encoding='utf-8') as f:
            self.rows = list(csv.DictReader(f))

    def test_empty_text_result_keeps_escaped_normalized_search_context(self):
        query = '  NO_SUCH_METRO\nدبی🙂  '
        result = lookup(search=query)
        text = format_text(result)
        expected = 'Name substring (normalized): ' + json.dumps(query.strip().casefold(), ensure_ascii=True)
        self.assertIn(expected, text.splitlines())
        self.assertIn('Matching metros: 0', text)
        self.assertIn('does not mean zero burden', text)
        self.assertEqual(len([line for line in text.splitlines()
                              if line.startswith('Name substring (normalized): ')]), 1)
        text.encode('ascii', errors='strict')

    def test_text_records_requested_codes_without_reordering_results(self):
        codes = [self.rows[-1]['cbsa_code'], self.rows[0]['cbsa_code']]
        result = lookup(codes=codes)
        original = json.dumps(result, sort_keys=True)
        text = format_text(result)
        self.assertIn('Requested CBSA codes: ' + ', '.join(codes), text.splitlines())
        self.assertEqual(result['rows'], [self.rows[0], self.rows[-1]])
        self.assertEqual(json.dumps(result, sort_keys=True), original)

    def test_ascii_terminal_text_keeps_values_and_no_match_distinct(self):
        environment = dict(os.environ, PYTHONIOENCODING='ascii:strict')
        for args in [('--code', self.rows[0]['cbsa_code']),
                     ('--search', 'NO_SUCH_METRO_123456')]:
            with self.subTest(args=args), tempfile.TemporaryDirectory() as folder:
                result = subprocess.run([sys.executable, '-B', str(ROOT / 'lookup_metro.py'),
                                         *args, '--format', 'text'], cwd=folder,
                                        env=environment, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                text = result.stdout.decode('ascii')
                self.assertNotIn(b'Traceback', result.stderr)
                if args[0] == '--code':
                    self.assertIn(self.rows[0]['rent_30plus_pct'] + '%', text)
                    self.assertIn(self.rows[0]['metro_name'], text)
                else:
                    self.assertIn('does not mean zero burden', text)

    def test_every_fixed_snapshot_text_label_encodes_as_ascii(self):
        result = lookup(codes=[row['cbsa_code'] for row in self.rows])
        self.assertEqual(len(result['rows']), len(self.rows))
        text = format_text(result)
        text.encode('ascii', errors='strict')
        for row in self.rows:
            self.assertIn(row['metro_name'], text)

    def test_downloaded_kit_text_runs_in_ascii_terminal(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'kit'
            with zipfile.ZipFile(ROOT / 'downloads/Metro-Rent-Burden-Offline-Lookup.zip') as archive:
                archive.extractall(target)
            result = subprocess.run([sys.executable, '-B', str(target / 'lookup_metro.py'),
                                     '--code', self.rows[0]['cbsa_code'], '--format', 'text'],
                                    cwd=folder, env=dict(os.environ, PYTHONIOENCODING='ascii:strict'),
                                    capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(self.rows[0]['metro_name'], result.stdout.decode('ascii'))

    def test_text_uses_exact_stored_values_and_denominator_labels(self):
        result = lookup(codes=[self.rows[0]['cbsa_code'], self.rows[-1]['cbsa_code']])
        text = format_text(result)
        self.assertLess(text.index(self.rows[0]['metro_name']), text.index(self.rows[-1]['metro_name']))
        for row in result['rows']:
            self.assertIn(row['rent_30plus_pct'] + '%', text)
            self.assertIn(row['rent_50plus_pct'] + '%', text)
            self.assertIn('Computable units (burden-share denominator): ' + row['computable_units'], text)
            self.assertIn('Not-computed share of ALL renter-occupied units: ' + row['not_computed_pct_all_renters'] + '%', text)
        self.assertIn('all 11 source estimate/MOE pairs', text)
        self.assertIn('not current asking rents', text)

    def test_text_keeps_blank_zero_and_no_match_distinct(self):
        result = lookup(codes=[self.rows[0]['cbsa_code']])
        # Synthetic formatting-only control; not an observed metro value.
        result['rows'][0]['rent_30plus_pct'] = ''
        result['rows'][0]['rent_50plus_pct'] = '0'
        text = format_text(result)
        self.assertIn('At least 30% of income in gross rent: Unavailable (blank in stored CSV)', text)
        self.assertIn('At least 50% of income in gross rent: 0%', text)
        self.assertNotIn('Unavailable (blank in stored CSV)%', text)
        empty = format_text(lookup(search='NO_SUCH_METRO_123456'))
        self.assertIn('Matching metros: 0', empty)
        self.assertIn('does not mean zero burden', empty)

    def test_cli_text_and_default_json_and_unknown_code(self):
        script = str(ROOT / 'lookup_metro.py')
        args = [sys.executable, '-B', script, '--code', self.rows[0]['cbsa_code']]
        with tempfile.TemporaryDirectory() as tmp:
            default = subprocess.run(args, cwd=tmp, capture_output=True, text=True)
            explicit = subprocess.run(args + ['--format', 'json'], cwd=tmp, capture_output=True, text=True)
            text = subprocess.run(args + ['--format', 'text'], cwd=tmp, capture_output=True, text=True)
            self.assertEqual(default.stdout, explicit.stdout)
            self.assertEqual(text.returncode, 0, text.stderr)
            self.assertEqual(text.stdout, format_text(json.loads(default.stdout)) + '\n')
            bad = subprocess.run(args + ['--code', '00000', '--format', 'text'], cwd=tmp, capture_output=True, text=True)
            self.assertEqual((bad.returncode, bad.stdout), (2, ''))

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
