import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('lookup_kit', ROOT / 'scripts/build_lookup_kit.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class OfflineLookupKit(unittest.TestCase):
    def test_exact_allowlist_manifest_and_immutable_sources(self):
        with zipfile.ZipFile(builder.TARGET) as archive:
            names = archive.namelist()
            self.assertEqual(len(names), 11)
            self.assertEqual(set(names), set(builder.FILES) | {'START-HERE.txt', 'CONTENTS.json'})
            self.assertIsNone(archive.testzip())
            manifest = json.loads(archive.read('CONTENTS.json'))
            self.assertEqual(manifest['source_commit'], builder.COMMIT)
            self.assertEqual(manifest['survey_year'], 2024)
            self.assertEqual(set(manifest['files']), set(names) - {'CONTENTS.json'})
            for name, digest in manifest['files'].items():
                self.assertEqual(hashlib.sha256(archive.read(name)).hexdigest(), digest, name)
            for name in builder.FILES:
                self.assertEqual(archive.read(name), subprocess.check_output(
                    ['git', 'show', builder.COMMIT + ':' + name], cwd=ROOT), name)
            self.assertEqual(archive.read('START-HERE.txt'), builder.GUIDE.read_bytes())

    def test_rebuild_preserves_every_logical_member(self):
        with zipfile.ZipFile(io.BytesIO(builder.payload())) as fresh, zipfile.ZipFile(builder.TARGET) as saved:
            self.assertEqual(fresh.namelist(), saved.namelist())
            for name in saved.namelist():
                self.assertEqual(fresh.read(name), saved.read(name), name)

    def test_extracted_lookup_runs_outside_folder_and_refuses_tampering(self):
        with tempfile.TemporaryDirectory() as folder:
            site = Path(folder) / 'kit'
            with zipfile.ZipFile(builder.TARGET) as archive:
                archive.extractall(site)
            before = {str(f.relative_to(site)): f.read_bytes() for f in site.rglob('*') if f.is_file()}
            script = site / 'lookup_metro.py'

            def call(*args):
                return subprocess.run([sys.executable, '-B', str(script), *args],
                                      cwd=folder, text=True, capture_output=True)

            text = call('--code', '38060', '--format', 'text')
            self.assertEqual(text.returncode, 0, text.stderr)
            self.assertIn('Phoenix', text.stdout)
            self.assertIn('2024', text.stdout)
            full = call('--code', '38060')
            self.assertEqual(full.returncode, 0, full.stderr)
            rows = list(csv.DictReader(io.StringIO(before['metro-rent-burden-2024.csv'].decode('utf-8'))))
            expected = next(row for row in rows if row['cbsa_code'] == '38060')
            report = json.loads(full.stdout)
            self.assertEqual(report['rows'], [expected])
            self.assertEqual(len(expected), 35)
            missing = call('--code', '00000')
            self.assertEqual(missing.returncode, 2)
            self.assertEqual(missing.stdout, '')
            self.assertEqual({str(f.relative_to(site)): f.read_bytes() for f in site.rglob('*') if f.is_file()}, before)
            data = site / 'metro-rent-burden-2024.csv'
            data.write_bytes(data.read_bytes() + b'\n')
            tampered = call('--code', '38060')
            self.assertEqual(tampered.returncode, 2)
            self.assertEqual(tampered.stdout, '')


if __name__ == '__main__':
    unittest.main()
