"""Regression tests for source drift and portable, offline-mocked downloads."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import download
from build import verify_snapshot

ROOT = Path(__file__).resolve().parent


class Snapshot(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'raw').mkdir()
        self.receipt = {'survey_year': 2024, 'sources': []}
        for name, data in [('2024-b25070.dat', b'GEO_ID|B25070_E001\nfixture|1\n'), ('2024-geographies.txt', b'FILEID|GEO_ID\nACSSF|fixture\n')]:
            (self.root / 'raw' / name).write_bytes(data)
            self.receipt['sources'].append({'file': 'raw/' + name, 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)})
        self.save()

    def save(self):
        (self.root / 'source-2024.json').write_text(json.dumps(self.receipt))

    def test_valid_snapshot(self):
        verify_snapshot(self.root, 2024)

    def test_each_changed_raw_file_is_rejected(self):
        for item in self.receipt['sources']:
            with self.subTest(file=item['file']):
                path = self.root / item['file']
                data = path.read_bytes()
                path.write_bytes(data + b'changed')
                with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                    verify_snapshot(self.root, 2024)
                path.write_bytes(data)

    def test_missing_receipt_is_rejected(self):
        (self.root / 'source-2024.json').unlink()
        with self.assertRaisesRegex(ValueError, 'Missing source receipt'):
            verify_snapshot(self.root, 2024)

    def test_missing_raw_file_is_rejected(self):
        (self.root / self.receipt['sources'][0]['file']).unlink()
        with self.assertRaisesRegex(ValueError, 'Missing source snapshot'):
            verify_snapshot(self.root, 2024)

    def test_wrong_year_is_rejected(self):
        self.receipt['survey_year'] = 2025
        self.save()
        with self.assertRaisesRegex(ValueError, 'year mismatch'):
            verify_snapshot(self.root, 2024)

    def test_duplicate_receipt_file_is_rejected(self):
        self.receipt['sources'][1] = self.receipt['sources'][0]
        self.save()
        with self.assertRaisesRegex(ValueError, 'unique raw files'):
            verify_snapshot(self.root, 2024)

    def test_wrong_byte_count_is_rejected(self):
        self.receipt['sources'][0]['bytes'] += 1
        self.save()
        with self.assertRaisesRegex(ValueError, 'byte-count mismatch'):
            verify_snapshot(self.root, 2024)

    def test_cli_rejects_changed_geography_before_touching_outputs(self):
        shutil.copyfile(ROOT / 'build.py', self.root / 'build.py')
        shutil.copyfile(ROOT / 'source-2024.json', self.root / 'source-2024.json')
        for name in ('2024-b25070.dat', '2024-geographies.txt'):
            shutil.copyfile(ROOT / 'raw' / name, self.root / 'raw' / name)
        geo = self.root / 'raw/2024-geographies.txt'
        content = geo.read_bytes()
        self.assertIn(b'Abilene, TX Metro Area', content)
        geo.write_bytes(content.replace(b'Abilene, TX Metro Area', b'Abilenx, TX Metro Area', 1))
        names = ('metro-rent-burden-2024.csv', 'summary-2024.json', 'excluded-cbsa-2024.json')
        for name in names:
            (self.root / name).write_bytes(b'keep-existing-output\n')
        result = subprocess.run([sys.executable, str(self.root / 'build.py'), '--year', '2024'], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Source snapshot hash mismatch', result.stderr)
        for name in names:
            self.assertEqual((self.root / name).read_bytes(), b'keep-existing-output\n')


class PortableDownload(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def run_download(self, side_effect):
        with patch.object(download, '__file__', str(self.root / 'download.py')), patch.object(sys, 'argv', ['download.py', '--year', '2024']), patch.object(download.urllib.request, 'urlopen', side_effect=side_effect) as request, contextlib.redirect_stdout(io.StringIO()):
            download.main()
        return request

    def test_fresh_2024_checkout_downloads_both_files(self):
        payloads = [b'GEO_ID|B25070_E001\nfixture|1\n', b'FILEID|GEO_ID\nACSSF|fixture\n']
        request = self.run_download([io.BytesIO(data) for data in payloads])
        self.assertEqual(request.call_count, 2)
        self.assertTrue(request.call_args_list[1].args[0].endswith('/documentation/Geos20241YR.txt'))
        self.assertEqual((self.root / 'raw/2024-geographies.txt').read_bytes(), payloads[1])
        verify_snapshot(self.root, 2024)

    def test_existing_snapshot_and_receipt_are_retained_without_network(self):
        (self.root / 'raw').mkdir()
        for name in ('2024-b25070.dat', '2024-geographies.txt'):
            (self.root / 'raw' / name).write_bytes(b'existing snapshot')
        (self.root / 'source-2024.json').write_bytes(b'existing receipt')
        request = self.run_download(AssertionError('Unexpected network'))
        request.assert_not_called()
        self.assertEqual((self.root / 'source-2024.json').read_bytes(), b'existing receipt')
        self.assertEqual((self.root / 'raw/2024-geographies.txt').read_bytes(), b'existing snapshot')

    def test_unexpected_response_is_not_saved_as_raw_data(self):
        with self.assertRaisesRegex(ValueError, 'Unexpected public table response'):
            self.run_download([io.BytesIO(b'<html>error</html>')])
        self.assertFalse((self.root / 'raw/2024-b25070.dat').exists())
        self.assertFalse((self.root / 'source-2024.json').exists())


if __name__ == '__main__':
    unittest.main()
