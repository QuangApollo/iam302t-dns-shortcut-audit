#!/usr/bin/env python3
"""Fetch the checksum-pinned CIC copy and prepare CTU for the compact public repo."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
CIC_SHA = '62ec5d632c9e665851c551487d6d1e2afbc7f8f55b62cac4649999dadafc89de'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    destination = ROOT / 'data/cic/CIC-Bell-DNS-EXF-2021.csv'
    if destination.exists():
        assert sha(destination) == CIC_SHA, 'Existing CIC bytes differ from the frozen source.'
    else:
        with urllib.request.urlopen('https://zenodo.org/api/records/18139853', timeout=60) as response:
            record = json.load(response)
        entry = [f for f in record['files'] if f['key'] == destination.name]
        assert len(entry) == 1
        url = entry[0]['links']['self']
        with urllib.request.urlopen(url, timeout=60) as response:
            raw = response.read()
        assert len(raw) == 46770313
        assert hashlib.sha256(raw).hexdigest() == CIC_SHA, 'Downloaded CIC SHA-256 mismatch.'
        assert hashlib.md5(raw).hexdigest() == '84fb059d04824f7167f5a2e4a579ba4c'
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)
    print('PASS checksum-pinned CIC copy', flush=True)
    subprocess.run([sys.executable, str(ROOT / 'source/prepare_ctu.py'), '--download'], check=True)
    subprocess.run([sys.executable, str(ROOT / 'source/prepare_ctu.py'), '--verify-binary-only'], check=True)


if __name__ == '__main__':
    main()
