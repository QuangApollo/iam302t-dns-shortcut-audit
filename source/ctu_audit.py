#!/usr/bin/env python3
"""CTU binary representation audit, with unchanged strings from verified originals."""
import os
for _name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[_name] = '1'
import csv
import gzip
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import f1_score
from audit_pipeline import metrics, environment, sha256

ROOT = Path(__file__).resolve().parents[1]


def features(s):
    labels = s.split('.')
    chars = s.replace('.', '')
    n = max(len(chars), 1)
    counts = Counter(chars)
    entropy = -sum((v / n) * math.log2(v / n) for v in counts.values())
    return [len(s), s.count('.'), max(map(len, labels)),
            sum(map(len, labels)) / len(labels),
            sum(c.isdigit() for c in chars) / n, chars.count('-') / n,
            entropy, len(counts) / n]


def load(split):
    metadata = json.loads((ROOT / 'results/ctu_preparation.json').read_text())
    path = ROOT / f'data/ctu/binary/{split}_binary.csv.gz'
    assert sha256(path) == metadata[split]['binary_sha256'], 'CTU binary bytes changed'
    names, y = [], []
    with gzip.open(path, 'rt', newline='') as f:
        for r in csv.DictReader(f):
            s = r['domain'].strip().lower().rstrip('.')
            assert s and r['class'] in ('0', '2')
            names.append(s)
            y.append(int(r['class'] == '2'))
    return names, np.asarray(y, dtype=np.int8)


def main():
    train, yt = load('train')
    test, y = load('test')
    assert (len(train), len(test), int(yt.sum()), int(y.sum())) == (950547, 237631, 6441, 1559)
    structure = []
    for split, names, labels in [('TRAIN', train, yt), ('TEST', test, y)]:
        for label in (0, 1):
            strings = [s for s, v in zip(names, labels) if v == label]
            dots = np.asarray([s.count('.') for s in strings])
            lengths = np.asarray([len(s) for s in strings])
            structure.append({'split': split, 'label': label, 'rows': len(strings),
                              'zero_dots': int((dots == 0).sum()),
                              'one_dot': int((dots == 1).sum()),
                              'two_plus_dots': int((dots >= 2).sum()),
                              'median_length': float(np.median(lengths)),
                              'p90_length': float(np.quantile(lengths, .9))})
    pd.DataFrame(structure).to_csv(ROOT / 'results/ctu_structure.csv', index=False)
    train_tokens = set(train)
    first = [s.split('.', 1)[0] for s in test]
    token_labels = defaultdict(set)
    for s, label in zip(train, yt):
        token_labels[s].add(int(label))
    overlap = []
    for label in (0, 1):
        idx = np.flatnonzero(y == label)
        tokens = [first[i] for i in idx]
        overlap.append({'label': label,
                        'full_string_matches_to_train': sum(test[i] in train_tokens for i in idx),
                        'first_label_matches_to_train': sum(s in train_tokens for s in tokens),
                        'first_label_label_disagreements': sum(s in train_tokens and label not in token_labels[s]
                                                               for s in tokens),
                        'repeated_first_label_rows_beyond_first': len(tokens) - len(set(tokens))})
    pd.DataFrame(overlap).to_csv(ROOT / 'results/ctu_overlap.csv', index=False)
    xtr = np.asarray([features(s) for s in train], dtype=np.float32)
    full = np.asarray([features(s) for s in test], dtype=np.float32)
    first_x = np.asarray([features(s) for s in first], dtype=np.float32)
    thresholds = [20, 30, 40, 50, 60, 80, 100]
    threshold = max(thresholds, key=lambda t: f1_score(yt, xtr[:, 0] > t, zero_division=0))
    rows = []
    for name, x in [('FULL_STRING', full), ('FIRST_LABEL', first_x)]:
        rows.append({'model': 'LENGTH', 'representation': name,
                     'threshold': threshold, **metrics(y, x[:, 0] > threshold)})
    for name, cols in [('LR8', list(range(8))), ('LR4', [4, 5, 6, 7])]:
        clf = Pipeline([('scale', StandardScaler()),
                        ('lr', LogisticRegression(C=.5, class_weight='balanced',
                                                   max_iter=2000, random_state=42))])
        clf.fit(xtr[:, cols], yt)
        for rep, x in [('FULL_STRING', full), ('FIRST_LABEL', first_x)]:
            rows.append({'model': name, 'representation': rep, 'threshold': .5,
                         **metrics(y, clf.predict(x[:, cols]))})
    # Preserve the two failed probes as diagnostic results, not useful detectors.
    suffix = defaultdict(Counter)
    family = defaultdict(Counter)
    for s, label in zip(train, yt):
        suffix[s.rsplit('.', 1)[-1]][int(label)] += 1
        family['.'.join(s.split('.')[-2:])][int(label)] += 1
    suffix_set = {s for s, c in suffix.items() if c[1] >= 10 and c[0] == 0}
    family_set = {s for s, c in family.items() if c[1] >= 5 and c[1] / sum(c.values()) >= .95}
    for name, selected, extract in [('LAST_LABEL', suffix_set, lambda s: s.rsplit('.', 1)[-1]),
                                     ('LAST_TWO_LABELS', family_set, lambda s: '.'.join(s.split('.')[-2:]))]:
        pred = np.asarray([extract(s) in selected for s in test])
        rows.append({'model': name, 'representation': 'FULL_STRING', 'threshold': None,
                     **metrics(y, pred)})
    pd.DataFrame(rows).to_csv(ROOT / 'results/ctu_results.csv', index=False)
    (ROOT / 'results/ctu_metadata.json').write_text(json.dumps({
        **{k: v for k, v in environment().items() if k != 'dataset_sha256'},
        'ctu_preparation_sha256': sha256(ROOT / 'results/ctu_preparation.json'),
        'selected_length_threshold_train_only': threshold,
        'train_unique_strings': len(train_tokens), 'test_unique_strings': len(set(test)),
        'suffix_train_selected': len(suffix_set), 'family_train_selected': len(family_set),
        'normalization': 'trim, lowercase, remove trailing dot; first-label sensitivity transforms test only',
        'scope': 'LR baselines, not a reproduction of CTU MC-CNN or a proof of complete DNS-transaction leakage.'}, indent=2) + '\n')
    print(pd.DataFrame(structure).to_string(index=False), flush=True)
    print(pd.DataFrame(overlap).to_string(index=False), flush=True)
    print(pd.DataFrame(rows)[['model', 'representation', 'FP', 'TP', 'f1', 'fpr']].to_string(index=False), flush=True)


if __name__ == '__main__':
    main()
