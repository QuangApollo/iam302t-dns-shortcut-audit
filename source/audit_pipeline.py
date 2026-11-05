#!/usr/bin/env python3
"""Reproducible, offline CIC audit. Frozen splits are bound to original CSV bytes."""
from __future__ import annotations

import os
for _name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
              'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_name] = '1'

import argparse
import ast
import hashlib
import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, accuracy_score, balanced_accuracy_score
from sklearn.model_selection import GroupKFold, GroupShuffleSplit, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/cic/CIC-Bell-DNS-EXF-2021.csv'
EXPECTED_SHA256 = '62ec5d632c9e665851c551487d6d1e2afbc7f8f55b62cac4649999dadafc89de'
DOMAIN = ['FQDN_count', 'subdomain_length', 'upper', 'lower', 'numeric',
          'entropy', 'special', 'labels', 'labels_max', 'labels_average',
          'len', 'subdomain', 'rr_name_entropy', 'rr_name_length']
QTYPE = ['A', 'AAAA', 'NS', 'CNAME', 'SOA', 'NULL', 'PTR', 'HINFO',
         'MX', 'TXT', 'SRV', 'OPT']
OTHER = ['rr_count', 'a_records', 'ttl_mean', 'ttl_variance', 'distinct_ns']
VARIANTS = ['FULL', 'NO_QTYPE', 'NO_DOMAIN', 'NO_BOTH',
            'NO_QTYPE_TTL', 'NO_BOTH_TTL']
SEED = 42


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def save_json(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n')


def environment():
    import matplotlib
    import scipy
    import joblib
    import threadpoolctl
    return {'python': platform.python_version(), 'numpy': np.__version__,
            'pandas': pd.__version__, 'scikit-learn': sklearn.__version__,
            'matplotlib': matplotlib.__version__, 'scipy': scipy.__version__,
            'joblib': joblib.__version__, 'threadpoolctl': threadpoolctl.__version__,
            'platform': platform.platform(), 'seed': SEED,
            'dataset_sha256': sha256(DATA)}


def read_data():
    digest = sha256(DATA)
    if EXPECTED_SHA256 != 'TO_BE_INITIALIZED' and digest != EXPECTED_SHA256:
        raise SystemExit('CSV bytes changed; use the original dataset for this experiment.')
    df = pd.read_csv(DATA, low_memory=False, encoding='utf-8-sig')
    assert df.shape == (228042, 42)
    assert set(df['label']) == {'heavy_benign', 'heavy_attack'}
    y = df['label'].map({'heavy_benign': 0, 'heavy_attack': 1}).to_numpy(np.int8)
    groups = (df['sld'].fillna('MISSING_SLD').astype(str).str.lower().str.strip()
              .replace('', 'MISSING_SLD').to_numpy())
    return df, y, groups


def checked_split(tr, te, n, groups=None):
    assert len(tr) > 0 and len(te) > 0
    assert len(np.unique(tr)) == len(tr) and len(np.unique(te)) == len(te)
    assert int(min(tr.min(), te.min())) >= 0
    assert int(max(tr.max(), te.max())) < n
    assert len(np.intersect1d(tr, te)) == 0
    assert len(tr) + len(te) == n
    if groups is not None:
        assert not set(groups[tr]) & set(groups[te])


def load_splits(df, y, groups):
    path = ROOT / 'splits/frozen_splits.npz'
    meta = json.loads((ROOT / 'splits/metadata.json').read_text())
    assert meta['dataset_sha256'] == sha256(DATA)
    assert meta['split_file_sha256'] == sha256(path)
    with np.load(path, allow_pickle=False) as f:
        ans = []
        for name in meta['protocols']:
            tr, te = f[name + '_train'], f[name + '_test']
            checked_split(tr, te, len(y), groups if name.startswith('GROUP_') else None)
            ans.append((name, tr, te))
    return ans


def freeze():
    target = ROOT / 'splits/frozen_splits.npz'
    if target.exists():
        raise SystemExit('Frozen splits already exist. Reuse them; do not silently regenerate.')
    df, y, groups = read_data()
    splits = [('ROW', *train_test_split(np.arange(len(y)), test_size=.3,
                                       random_state=SEED, stratify=y))]
    splits += [('GROUP_' + str(k), tr, te) for k, (tr, te) in enumerate(
        GroupKFold(n_splits=3).split(np.zeros(len(y)), y, groups), 1)]
    # A separate, input-only grouping diagnostic. Labels never select this split.
    vec = pd.util.hash_pandas_object(df.drop(columns='label'), index=False).to_numpy()
    tr, te = next(GroupShuffleSplit(n_splits=1, test_size=.3, random_state=SEED)
                  .split(np.zeros(len(y)), groups=vec))
    splits.append(('EXACT_VECTOR_GROUP', tr, te))
    arrays, rows = {}, []
    for name, tr, te in splits:
        checked_split(tr, te, len(y), groups if name.startswith('GROUP_') else None)
        assert len(np.unique(y[tr])) == len(np.unique(y[te])) == 2
        if name == 'EXACT_VECTOR_GROUP':
            assert not set(vec[tr]) & set(vec[te])
        arrays[name + '_train'] = tr.astype(np.int32)
        arrays[name + '_test'] = te.astype(np.int32)
        rows.append({'protocol': name, 'train_n': len(tr), 'test_n': len(te),
                     'test_benign': int((y[te] == 0).sum()),
                     'test_attack': int((y[te] == 1).sum()),
                     'shared_sld': len(set(groups[tr]) & set(groups[te])),
                     'shared_complete_nonlabel_vectors': len(set(vec[tr]) & set(vec[te]))})
    np.savez_compressed(target, **arrays)
    save_json(ROOT / 'splits/metadata.json', {
        **environment(), 'split_file_sha256': sha256(target),
        'protocols': [s[0] for s in splits],
        'rule': 'ROW seed42 stratified70/30; ALL GroupKFold3; exact-vector GroupShuffleSplit70/30 seed42',
        'selection': 'No score-based or candidate-label-composition selection. All three group folds retained.',
        'exact_vector_key': 'pandas hash of all 41 original nonlabel columns; original row order retained.'})
    pd.DataFrame(rows).to_csv(ROOT / 'results/split_inventory.csv', index=False)
    save_json(ROOT / 'ENVIRONMENT.json', environment())
    print(pd.DataFrame(rows).to_string(index=False), flush=True)


def metrics(y, pred):
    tn, fp, fn, tp = map(int, confusion_matrix(y, pred, labels=[0, 1]).ravel())
    return {'TN': tn, 'FP': fp, 'FN': fn, 'TP': tp,
            'accuracy': (tn + tp) / len(y),
            'precision': tp / (tp + fp) if tp + fp else 0.,
            'recall': tp / (tp + fn) if tp + fn else 0.,
            'f1': 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.,
            'fpr': fp / (fp + tn) if fp + tn else 0.}


def inputs(df):
    x = pd.DataFrame(index=df.index)
    for c in DOMAIN + OTHER + [q + '_frequency' for q in QTYPE]:
        x[c] = pd.to_numeric(df[c], errors='coerce')
    raw = df['rr_type'].fillna('').astype(str).str.upper()
    for q in QTYPE:
        x['raw_type_' + q] = raw.str.contains(r'\b' + q + r'\b', regex=True).astype(float)
    return x.replace([np.inf, -np.inf], np.nan).astype(np.float32)


def feature_sets(x, tr, model):
    d = DOMAIN.copy()
    q = [c for c in x if c.endswith('_frequency') or c.startswith('raw_type_')]
    o = OTHER.copy()
    if model == 'LR':
        valid = [c for c in x if x.iloc[tr][c].dropna().size >= 10
                 and x.iloc[tr][c].dropna().nunique() > 1]
        d, q, o = [[c for c in cols if c in valid] for cols in (d, q, o)]
    return {'FULL': d + q + o, 'NO_QTYPE': d + o, 'NO_DOMAIN': q + o,
            'NO_BOTH': o, 'NO_QTYPE_TTL': d + [c for c in o if not c.startswith('ttl_')],
            'NO_BOTH_TTL': [c for c in o if not c.startswith('ttl_')]}


def experiments(model):
    df, y, groups = read_data()
    x = inputs(df)
    result, inventories = [], {}
    (ROOT / 'results/predictions').mkdir(exist_ok=True)
    for name, tr, te in load_splits(df, y, groups):
        # Exact-vector split adds a focused FULL diagnostic, keeping compute bounded.
        variants = ['FULL'] if name == 'EXACT_VECTOR_GROUP' else VARIANTS
        fs = feature_sets(x, tr, model)
        inventories[name] = fs
        for variant in variants:
            cols = fs[variant]
            if model == 'RF':
                clf = Pipeline([('fill', SimpleImputer(strategy='constant', fill_value=0,
                                                      keep_empty_features=True)),
                                ('model', RandomForestClassifier(n_estimators=100,
                                 max_depth=16, min_samples_leaf=2, random_state=SEED, n_jobs=2))])
            else:
                clf = Pipeline([('fill', SimpleImputer(strategy='constant', fill_value=0,
                                                      keep_empty_features=True)),
                                ('scale', StandardScaler()),
                                ('model', LogisticRegression(C=.5, class_weight='balanced',
                                 max_iter=2000, random_state=SEED))])
            clf.fit(x.loc[tr, cols], y[tr])
            pred = clf.predict(x.loc[te, cols])
            r = {'model': model, 'protocol': name, 'variant': variant,
                 'train_n': len(tr), 'test_n': len(te), 'n_features': len(cols),
                 **metrics(y[te], pred)}
            result.append(r)
            np.savez_compressed(ROOT / f'results/predictions/{model}_{name}_{variant}.npz',
                                test_index=te, actual=y[te], predicted=pred.astype(np.int8))
            # Checkpoints are separate per model, preventing parallel write races.
            pd.DataFrame(result).to_csv(ROOT / f'results/{model.lower()}_results.csv', index=False)
            print(f'{model} {name} {variant}: F1={r["f1"]:.6f} '
                  f'FPR={r["fpr"]:.6f} FP={r["FP"]} TP={r["TP"]}', flush=True)
    save_json(ROOT / f'results/{model.lower()}_metadata.json', {
        **environment(), 'split_sha256': sha256(ROOT / 'splits/frozen_splits.npz'),
        'features_by_split': inventories, 'imputation': 'constant zero; train fit only',
        'parameters': clf.named_steps['model'].get_params()})


def audit():
    df, y, groups = read_data()
    h = pd.util.hash_pandas_object(df.drop(columns='label'), index=False).to_numpy()
    t = pd.DataFrame({'key': h, 'attack': y})
    c = t.groupby('key')['attack'].agg(['size', 'sum', 'nunique'])
    conflicting = c[c['nunique'] > 1].copy()
    conflicting['benign'] = conflicting['size'] - conflicting['sum']
    conflicting = conflicting.rename(columns={'sum': 'attack', 'size': 'rows'})
    conflicting.reset_index().to_csv(ROOT / 'results/conflicting_vectors.csv', index=False)
    # Verify the hash-based conflict groups against exact original cell equality.
    for _, idx in t[t.key.isin(conflicting.index)].groupby('key').groups.items():
        assert len(df.loc[idx].drop(columns='label').drop_duplicates()) == 1
    summary = {'n_rows': len(df), 'benign': int((y == 0).sum()), 'attack': int(y.sum()),
               'duplicate_full_rows_beyond_first': int(df.duplicated().sum()),
               'duplicate_full_rows_percent': 100 * float(df.duplicated().mean()),
               'distinct_nonlabel_vectors': len(c), 'conflicting_nonlabel_vector_groups': len(conflicting),
               'rows_in_conflicting_vectors': int(conflicting.rows.sum()),
               'empirical_min_errors_deterministic_all41': int(np.minimum(c['sum'], c['size'] - c['sum']).sum()),
               'interpretation': 'Feature-equivalent records with different labels are not by themselves proof of mislabeling. '
                                 'The empirical all-row error floor is not a bound for a separately sampled test set.'}
    split_overlap, fold_groups = [], []
    group_counts = pd.crosstab(pd.Series(groups, name='sld'), pd.Series(y, name='label'))
    group_counts.columns = ['benign', 'attack']
    group_counts['total'] = group_counts.sum(axis=1)
    group_counts.sort_values('total', ascending=False).to_csv(ROOT / 'results/sld_group_profile.csv')
    for name, tr, te in load_splits(df, y, groups):
        seen = np.isin(h[te], h[tr])
        split_overlap.append({'protocol': name, 'test_n': len(te),
                              'test_rows_matching_train_nonlabel_vector': int(seen.sum()),
                              'percent': 100 * float(seen.mean())})
        if name.startswith('GROUP_'):
            for token, n in pd.Series(groups[te]).value_counts().head(5).items():
                mask = groups[te] == token
                fold_groups.append({'protocol': name, 'sld': token, 'rows': int(n),
                                    'benign': int((y[te][mask] == 0).sum()),
                                    'attack': int(y[te][mask].sum())})
    pd.DataFrame(split_overlap).to_csv(ROOT / 'results/vector_overlap.csv', index=False)
    pd.DataFrame(fold_groups).to_csv(ROOT / 'results/fold_dominant_groups.csv', index=False)
    save_json(ROOT / 'results/dataset_audit.json', summary)
    print(json.dumps(summary, indent=2), flush=True)


def proxies():
    df, y, groups = read_data()
    q = df['rr_type'].fillna('').str.contains(r'\bPTR\b').to_numpy(np.int8)
    rows = []
    rule = df.ttl_mean.isin([1, 255]).to_numpy(np.int8)
    rows.append({'protocol': 'ALL_ROWS_POST_HOC', 'features': 'TTL rule in {1,255}',
                 'task': 'PTR-versus-other', 'accuracy': accuracy_score(q, rule),
                 'balanced_accuracy': balanced_accuracy_score(q, rule), **metrics(q, rule)})
    for name, tr, te in load_splits(df, y, groups):
        if name == 'EXACT_VECTOR_GROUP':
            continue
        for title, cols in [('TTL_ONLY', ['ttl_mean', 'ttl_variance']),
                            ('OTHER_ONLY', OTHER),
                            ('OTHER_WITHOUT_TTL', [c for c in OTHER if not c.startswith('ttl_')])]:
            clf = DecisionTreeClassifier(max_depth=3, random_state=SEED)
            clf.fit(df.loc[tr, cols], q[tr])
            pred = clf.predict(df.loc[te, cols])
            rows.append({'protocol': name, 'features': title, 'task': 'PTR-versus-other',
                         'accuracy': accuracy_score(q[te], pred),
                         'balanced_accuracy': balanced_accuracy_score(q[te], pred), **metrics(q[te], pred)})
    pd.DataFrame(rows).to_csv(ROOT / 'results/qtype_proxy_results.csv', index=False)
    print(pd.DataFrame(rows)[['protocol', 'features', 'accuracy', 'balanced_accuracy']].to_string(index=False), flush=True)


def reference_baseline():
    """A closer single-stage feature inventory, still NOT the published hybrid."""
    df, y, groups = read_data()
    x = df.drop(columns='label').copy()
    # Original release describes averaging unique_ttl before categorical encoding.
    def ttl_mean(value):
        seq = ast.literal_eval(value) if isinstance(value, str) else value
        return float(np.mean(seq)) if isinstance(seq, (list, tuple)) and len(seq) else 0.
    x['unique_ttl'] = x['unique_ttl'].map(ttl_mean)
    categorical = list(x.select_dtypes(include='object'))
    for c in categorical:
        x[c] = x[c].fillna('').astype(str)
    numeric = [c for c in x if c not in categorical]
    x[numeric] = x[numeric].replace([np.inf, -np.inf], np.nan).fillna(0.)
    dom = DOMAIN + ['longest_word', 'sld']
    qtype = ['rr_type'] + [q + '_frequency' for q in QTYPE]
    variants = {'FULL': list(x), 'NO_QTYPE': [c for c in x if c not in qtype],
                'NO_DOMAIN': [c for c in x if c not in dom],
                'NO_BOTH': [c for c in x if c not in dom + qtype]}
    _, tr, te = load_splits(df, y, groups)[0]
    result = []
    for variant, cols in variants.items():
        cat = [c for c in cols if c in categorical]
        num = [c for c in cols if c in numeric]
        pre = ColumnTransformer([('numeric', 'passthrough', num),
                                 ('categorical', OrdinalEncoder(handle_unknown='use_encoded_value',
                                                               unknown_value=-1), cat)])
        clf = Pipeline([('pre', pre), ('rf', RandomForestClassifier(n_estimators=100,
                         random_state=SEED, n_jobs=2))])
        clf.fit(x.loc[tr, cols], y[tr])
        pred = clf.predict(x.loc[te, cols])
        r = {'model': 'RF_REFERENCE_INVENTORY', 'protocol': 'ROW', 'variant': variant,
             'n_features_before_encoding': len(cols), **metrics(y[te], pred)}
        result.append(r)
        print(r, flush=True)
    pd.DataFrame(result).to_csv(ROOT / 'results/reference_inventory_results.csv', index=False)
    save_json(ROOT / 'results/reference_inventory_metadata.json', {
        **environment(), 'categorical_fields': categorical,
        'encoding': 'OrdinalEncoder fitted on train only; unknown=-1',
        'parameters': {'n_estimators': 100, 'max_depth': None, 'min_samples_leaf': 1, 'seed': SEED},
        'scope': 'Single-stage full CSV feature inventory; missing stateless-first gating and raw timed packet windows. '
                 'Not exact reproduction of DOI 10.1145/3507509.3507520.'})


def verify():
    df, y, groups = read_data()
    splits = {name: (tr, te) for name, tr, te in load_splits(df, y, groups)}
    checks = []
    for model in ['LR', 'RF']:
        data = pd.read_csv(ROOT / f'results/{model.lower()}_results.csv')
        assert len(data) == len(VARIANTS) * 4 + 1
        for _, row in data.iterrows():
            p = ROOT / f'results/predictions/{model}_{row.protocol}_{row.variant}.npz'
            with np.load(p, allow_pickle=False) as r:
                assert np.array_equal(r['test_index'], splits[row.protocol][1])
                assert np.array_equal(r['actual'], y[r['test_index']])
                expected = metrics(r['actual'], r['predicted'])
            for key, val in expected.items():
                assert abs(float(row[key]) - val) < 1e-9, (model, row.protocol, row.variant, key)
        checks.append(f'PASS {model}: all 25 confusion matrices and metrics match saved row-level predictions')
    checks.append('PASS: dataset SHA-256 and frozen split SHA-256 match; all SLD folds are disjoint')
    save_json(ROOT / 'results/validation.json', {'checks': checks, **environment()})
    print('\n'.join(checks), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage', choices=['freeze', 'audit', 'proxies', 'experiments', 'reference', 'verify'])
    p.add_argument('--model', choices=['LR', 'RF'], default='RF')
    args = p.parse_args()
    {'freeze': freeze, 'audit': audit, 'proxies': proxies,
     'experiments': lambda: experiments(args.model), 'reference': reference_baseline,
     'verify': verify}[args.stage]()
