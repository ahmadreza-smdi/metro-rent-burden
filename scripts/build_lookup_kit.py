"""Build the fixed-snapshot, allowlisted offline lookup download; no network."""
from pathlib import Path
import hashlib
import io
import json
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
COMMIT = '59be3b664fe52475040ad365a3aff013f751b66e'
FILES = (
    'lookup_metro.py', 'verify_dictionary.py', 'metro-rent-burden-2024.csv',
    'data-dictionary.json', 'raw/2024-b25070-variables.json', 'LICENSE',
    'CITATION.cff', 'READING-GUIDE.txt', 'DATA-DICTIONARY.txt',
)
GUIDE = ROOT / 'docs/offline-lookup/START-HERE.txt'
TARGET = ROOT / 'downloads/Metro-Rent-Burden-Offline-Lookup.zip'


def payload():
    # Read immutable Git blobs, not platform-normalized working copies or newer data.
    contents = {name: subprocess.check_output(
        ['git', 'show', COMMIT + ':' + name], cwd=ROOT) for name in FILES}
    contents['START-HERE.txt'] = GUIDE.read_bytes()
    manifest = {
        'format': 'personal-metro-lookup-kit-v1',
        'author': 'Ahmadreza Samadi', 'author_url': 'https://a-samadi.com/about.html',
        'source_repository': 'https://github.com/ahmadreza-smdi/metro-rent-burden',
        'source_commit': COMMIT, 'survey_year': 2024,
        'scope': 'Offline fixed-snapshot lookup companion; not a full raw-source rebuild or a new versioned study release.',
        'files': {name: hashlib.sha256(raw).hexdigest() for name, raw in contents.items()},
    }
    contents['CONTENTS.json'] = (json.dumps(manifest, indent=2) + '\n').encode('utf-8')
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, raw in contents.items():
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 17, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, raw)
    return output.getvalue()


if __name__ == '__main__':
    raw = payload()
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_bytes(raw)
    print('Built 11-file fixed ACS 2024 lookup companion; no new observations or release.')
