#!/usr/bin/env python3
"""Record pinned CTU-associated preprocessing provenance without running its model."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

import audit_pipeline as audit

COMMIT = '769e3466f90173b663aa1fe3008e7a70295fbdfd'
FILES = {
    'preprocess.R': '32984c9db1307b056ffb9a702e24f8fae081538c24f2b3cfdc05e6b937e3273a',
    'deepseq_classifier.R': '0777c9407156191ec80c4590de6f6e7f889ff56b73f87efc688236d4a5410bcc',
    'config.R': '437d5ae7c2565503ee08879532d4717a3cc9db665940b8ef37da223d8c605361',
    'model_mc_cnn_asai.R': '35d3cd20444fa3a8ee987093027a946852f49dfe8fea024b0b75e63d24625e3e',
}


def main(directory, download):
    records = []
    for name, expected in FILES.items():
        url = f'https://raw.githubusercontent.com/harpomaxx/deepseq/{COMMIT}/{name}'
        path = directory / name
        if not path.exists():
            if not download:
                raise SystemExit('Missing pinned source; use --download or provide --source-dir.')
            directory.mkdir(parents=True, exist_ok=True)
            with urllib.request.urlopen(url, timeout=60) as response:
                path.write_bytes(response.read())
        raw = path.read_bytes()
        actual = hashlib.sha256(raw).hexdigest()
        assert actual == expected, (name, actual)
        lines = raw.decode('utf-8').splitlines()
        tokens = ['tokenize <-', 'padded_token<-', 'build_dataset<-', 'build_train_test<-',
                  'make_option("--maxlen"', 'testset<-read_valid_csv', 'test_dataset_keras<-build_dataset']
        locations = {token: [i+1 for i, line in enumerate(lines) if token in line]
                     for token in tokens if any(token in line for line in lines)}
        records.append({'file': name, 'url': url, 'sha256': actual, 'line_locations': locations})
    audit.save_json(audit.ROOT / 'results/revision_v2/ctu_source_trace.json', {
        'repository': 'https://github.com/harpomaxx/deepseq', 'commit': COMMIT,
        'inspected_at': '2026-11-03', 'files': records,
        'verified_behavior': ['Character tokenization followed by end padding/end truncation',
                              'Command-line maximum-length default 45',
                              'External test file uses the same build_dataset function'],
        'no_suffix_removal_in_inspected_preprocessing': True,
        'scope': 'Source inspection and first-45-character exposure check. Not execution of the R pipeline, verification of the exact historical vocabulary/configuration, or reproduction of a neural checkpoint.',
        'publication_trace': {
            '2019': 'Table 3 per-class test supports match the released test files; narrative 70/30 differs from released approximately 80/20 counts. Matching supports alone do not identify the entire run.',
            '2020': 'The follow-up explicitly describes a new five-tool dataset; the three-tool release finding is not automatically attributed to that dataset.'},
        'source_sha256': audit.sha256(__file__),
    })
    print('PASS pinned CTU-associated source hashes; recorded source-inspection scope.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', type=Path, default=audit.ROOT / 'data/ctu/associated_source')
    parser.add_argument('--download', action='store_true')
    args = parser.parse_args()
    main(args.source_dir, args.download)
