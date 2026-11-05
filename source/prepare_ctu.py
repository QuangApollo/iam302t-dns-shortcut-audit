#!/usr/bin/env python3
"""Download original CTU files, check publisher MD5, and create binary CSVs.

Only class filtering is applied; domain strings are copied unchanged.
Existing downloads are verified before reuse. A failed digest stops processing.
"""
import argparse
import csv
import gzip
import hashlib
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    'train': ('train_combined_multiclass.csv.gz', 'c30a49c6f362e0c2dffe3881504a6825'),
    'test': ('test_combined_multiclass.csv.gz', 'ce52df239c4245ffaa15c642b8b0b625'),
}


def digest(path, algorithm):
    h = hashlib.new(algorithm)
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--download', action='store_true', help='Download missing original public files')
    p.add_argument('--verify-binary-only', action='store_true', help='Verify packaged binary files without downloading raw files')
    args = p.parse_args()
    raw = ROOT / 'data/ctu/raw'
    binary = ROOT / 'data/ctu/binary'
    raw.mkdir(parents=True, exist_ok=True)
    binary.mkdir(parents=True, exist_ok=True)
    if args.verify_binary_only:
        metadata = json.loads((ROOT / 'results/ctu_preparation.json').read_text())
        for split in FILES:
            path = binary / f'{split}_binary.csv.gz'
            if digest(path, 'sha256') != metadata[split]['binary_sha256']:
                raise SystemExit(f'Binary SHA-256 mismatch: {split}')
            print('PASS packaged binary SHA-256:', split, flush=True)
        return
    result = {}
    for split, (name, expected) in FILES.items():
        src = raw / name
        url = f'https://zenodo.org/records/6508640/files/{name}?download=1'
        if not src.exists():
            if not args.download:
                raise SystemExit(f'Missing {src}; rerun with --download or supply the unchanged original file.')
            part = src.with_suffix(src.suffix + '.part')
            print('Downloading', name, flush=True)
            with urllib.request.urlopen(url, timeout=60) as response, part.open('wb') as out:
                for b in iter(lambda: response.read(1024 * 1024), b''):
                    out.write(b)
            part.replace(src)
        if digest(src, 'md5') != expected:
            raise SystemExit(f'Publisher MD5 mismatch: {name}')
        counts = {'0': 0, '1': 0, '2': 0}
        outpath = binary / f'{split}_binary.csv.gz'
        # mtime=0 makes the gzip header deterministic.
        import io
        with gzip.open(src, 'rt', newline='') as f, outpath.open('wb') as out:
            with gzip.GzipFile(filename='', mode='wb', fileobj=out, mtime=0) as zipped:
                with io.TextIOWrapper(zipped, encoding='utf-8', newline='') as g:
                    writer = csv.DictWriter(g, fieldnames=['domain', 'class'])
                    writer.writeheader()
                    for row in csv.DictReader(f):
                        label = row['class'].strip()
                        if label not in counts:
                            raise ValueError('Unexpected class: ' + label)
                        counts[label] += 1
                        if label in ('0', '2'):
                            writer.writerow({'domain': row['domain'], 'class': label})
        result[split] = {'source_url': url, 'publisher_md5': expected,
                         'source_sha256': digest(src, 'sha256'),
                         'binary_sha256': digest(outpath, 'sha256'),
                         'original_label_counts': counts,
                         'binary_rows': counts['0'] + counts['2'],
                         'transformation': 'Keep class 0 and 2. Copy domain field unchanged.'}
        print(split, result[split], flush=True)
    (ROOT / 'results/ctu_preparation.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
