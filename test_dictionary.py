"""Negative controls for the dictionary consumer, with synthetic row mutations."""
import csv
import json
from pathlib import Path
import tempfile
import unittest
from verify_dictionary import validate_rows, verify

ROOT = Path(__file__).resolve().parent


class DictionaryChecks(unittest.TestCase):
    def setUp(self):
        with (ROOT / 'metro-rent-burden-2024.csv').open(newline='', encoding='utf-8') as f:
            self.row = next(csv.DictReader(f))

    def test_snapshot(self):
        self.assertEqual(verify()['derived_percentage_checks'], 1158)

    def test_fraction_is_not_percent(self):
        row = dict(self.row); row['rent_30plus_pct'] = '0.578399'
        with self.assertRaisesRegex(ValueError, 'percentage mismatch'):
            validate_rows([row])

    def test_unknown_share_uses_all_renters(self):
        row = dict(self.row)
        row['not_computed_pct_all_renters'] = str(100 * int(row['not_computed_units']) / int(row['computable_units']))
        with self.assertRaisesRegex(ValueError, 'percentage mismatch'):
            validate_rows([row])

    def test_source_sentinel_is_not_zero(self):
        row = dict(self.row); row['B25070_M002'] = '-222222222'
        with self.assertRaisesRegex(ValueError, 'nonnegative count'):
            validate_rows([row])

    def test_unavailable_is_not_zero(self):
        row = dict(self.row); row['rent_50plus_pct'] = ''
        with self.assertRaises(ValueError):
            validate_rows([row])

    def test_duplicate_geography(self):
        with self.assertRaisesRegex(ValueError, 'duplicate geography'):
            validate_rows([self.row, dict(self.row)])

    def test_changed_source_label(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            names = ['data-dictionary.json', 'metro-rent-burden-2024.csv', 'raw/2024-b25070-variables.json']
            for name in names:
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                (root / name).write_bytes((ROOT / name).read_bytes())
            dictionary = json.loads((root / names[0]).read_text(encoding='utf-8'))
            dictionary['fields'][13]['source_label'] = 'An invented source label'
            (root / names[0]).write_text(json.dumps(dictionary), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Source-label'):
                verify(root)


if __name__ == '__main__':
    unittest.main()
