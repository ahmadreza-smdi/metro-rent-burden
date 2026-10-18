"""JSON remains lossless when stdout is constrained to ASCII."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

from lookup_metro import ROOT, lookup


class JSONStream(unittest.TestCase):
    def run_cli(self, script, args, cwd):
        return subprocess.run([sys.executable, '-B', str(script), *args], cwd=cwd,
                              env=dict(os.environ, PYTHONIOENCODING='ascii:strict'),
                              capture_output=True)

    def assert_report(self, run, expected):
        self.assertEqual((run.returncode, run.stderr), (0, b''))
        self.assertEqual(json.loads(run.stdout.decode('ascii')), expected)

    def test_default_json_in_ascii_stream_keeps_all_stored_fields(self):
        expected = lookup(codes=['10420'])
        source = ROOT / expected['snapshot']['file']
        before = hashlib.sha256(source.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory() as folder:
            run = self.run_cli(ROOT / 'lookup_metro.py', ['--code', '10420'], folder)
        self.assert_report(run, expected)
        self.assertEqual(before, hashlib.sha256(source.read_bytes()).hexdigest())

    def test_non_ascii_query_survives_ascii_json_without_false_zero_burden(self):
        query = 'بررسی ناموجود 🧪'
        with tempfile.TemporaryDirectory() as folder:
            run = self.run_cli(ROOT / 'lookup_metro.py', ['--search', query], folder)
        self.assert_report(run, lookup(search=query))
        result = json.loads(run.stdout.decode('ascii'))
        self.assertEqual(result['selection']['name_contains'], query.casefold())
        self.assertEqual(result['rows'], [])
        self.assertIn('not zero burden', result['interpretation']['missing_selection'])

    def test_extracted_offline_kit_default_json_matches_source_reports(self):
        with tempfile.TemporaryDirectory() as folder:
            kit = Path(folder) / 'kit'
            with zipfile.ZipFile(ROOT / 'downloads/Metro-Rent-Burden-Offline-Lookup.zip') as archive:
                archive.extractall(kit)
            cases = [(['--code', '10420'], lookup(codes=['10420'])),
                     (['--search', 'بررسی ناموجود 🧪'], lookup(search='بررسی ناموجود 🧪'))]
            for args, expected in cases:
                with self.subTest(args=args):
                    self.assert_report(self.run_cli(kit / 'lookup_metro.py', args, folder), expected)


if __name__ == '__main__':
    unittest.main()
