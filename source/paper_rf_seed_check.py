#!/usr/bin/env python3
"""Measure RF seed sensitivity on ALL frozen coarse-token folds.

The default experiment is fixed before fitting: 5 seeds x 3 folds x 2
feature sets = 30 cases. It measures stochastic-model stability, not new
independent traffic populations. Existing split indices are never regenerated.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import time

import numpy as np
import pandas as pd

import audit_pipeline as audit
from revision_v2_diagnostics import pipeline

SEEDS = [42, 0, 1, 7, 2026]
PROTOCOLS = ['GROUP_1', 'GROUP_2', 'GROUP_3']
VARIANTS = ['FULL', 'NO_DOMAIN']


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def save_case(path, plan_hash, seed, protocol, variant, test, actual, predicted, score):
    buffer = io.BytesIO()
    np.savez_compressed(buffer, plan_sha256=np.asarray(plan_hash), seed=np.asarray(seed),
                        protocol=np.asarray(protocol), variant=np.asarray(variant),
                        test_index=test, actual=actual, predicted=predicted,
                        attack_probability=score)
    path.write_bytes(buffer.getvalue())


def main(output, resume, plan_only, smoke):
    frame, actual, groups = audit.read_data()
    inputs = audit.inputs(frame)
    splits = {name: (train, test) for name, train, test in audit.load_splits(frame, actual, groups)}
    assert 'sld' not in inputs
    cases = [(s, p, v) for s in SEEDS for p in PROTOCOLS for v in VARIANTS]
    if smoke:
        cases = [(42, 'GROUP_2', 'FULL')]
    plan = {
        'schema': 'paper-rf-seeds-v1', 'mode': 'smoke' if smoke else 'full',
        'dataset_sha256': audit.sha256(audit.DATA),
        'split_sha256': audit.sha256(audit.ROOT / 'splits/frozen_splits.npz'),
        'source_sha256': audit.sha256(__file__),
        'pipeline_source_sha256': audit.sha256(audit.ROOT / 'source/revision_v2_diagnostics.py'),
        'audit_source_sha256': audit.sha256(audit.ROOT / 'source/audit_pipeline.py'),
        'seeds': SEEDS, 'protocols': PROTOCOLS, 'variants': VARIANTS,
        'cases': [{'seed': s, 'protocol': p, 'variant': v} for s, p, v in cases],
        'expected_cases': len(cases),
        'rf_parameters': {'n_estimators': 100, 'max_depth': 16,
                          'min_samples_leaf': 2, 'class_weight': None, 'n_jobs': 2},
        'preprocessing': 'Same zero imputation and exact RF feature inventory as the frozen baseline.',
        'threshold': 'Default classifier predict; no threshold tuning or best-seed selection.',
        'analysis': 'Report every seed and fold, per-fold min/median/max F1, and paired FULL-minus-NO_DOMAIN F1. Seeds reuse the same test rows; no independent-sample confidence interval.',
        'group_scope': 'Exact coarse-token holdouts; not validated registered-domain or capture holdouts.',
    }
    encoded = json.dumps(plan, sort_keys=True, separators=(',', ':')).encode()
    plan_hash = hashlib.sha256(encoded).hexdigest()
    output.mkdir(parents=True, exist_ok=True)
    plan_file = output / 'plan.json'
    if plan_file.exists():
        assert json.loads(plan_file.read_text()) == plan, 'Existing output has a different plan; use a separate output folder.'
    else:
        write_json(plan_file, plan)
    if plan_only:
        print(f'PLAN SAVED: {len(cases)} cases; no models fitted. SHA-256={plan_hash}', flush=True)
        return
    metadata_file = output / 'run_metadata.json'
    environment = audit.environment()
    if metadata_file.exists():
        previous = json.loads(metadata_file.read_text())
        assert previous['plan_sha256'] == plan_hash
        assert previous['environment'] == environment, 'Resume with the original environment, or use a new output folder.'
    else:
        write_json(metadata_file, {'plan_sha256': plan_hash,
                   'started_at_utc': datetime.now(timezone.utc).isoformat(),
                   'environment': environment,
                   'scope': 'RF stochastic-model stability on fixed test rows, not independent deployment validation.'})
    rows = []
    for number, (seed, protocol, variant) in enumerate(cases, 1):
        train, test = splits[protocol]
        path = output / f'RF_{protocol}_{variant}_seed_{seed}.npz'
        start = time.perf_counter()
        if path.exists():
            if not resume:
                raise SystemExit(f'{path.name} exists. Use --resume to validate and reuse it.')
            with np.load(path, allow_pickle=False) as saved:
                assert str(saved['plan_sha256']) == plan_hash
                assert int(saved['seed']) == seed
                assert str(saved['protocol']) == protocol and str(saved['variant']) == variant
                assert np.array_equal(saved['test_index'], test)
                assert np.array_equal(saved['actual'], actual[test])
                predicted = saved['predicted'].copy()
                probability = saved['attack_probability'].copy()
            origin = 'cached'
        else:
            columns = audit.feature_sets(inputs, train, 'RF')[variant]
            clf = pipeline('RF')
            clf.named_steps['model'].set_params(random_state=seed)
            clf.fit(inputs.loc[train, columns], actual[train])
            predicted = clf.predict(inputs.loc[test, columns]).astype(np.int8)
            probability = clf.predict_proba(inputs.loc[test, columns])[:, 1]
            save_case(path, plan_hash, seed, protocol, variant, test,
                      actual[test], predicted, probability)
            origin = 'fitted'
        assert predicted.shape == probability.shape == actual[test].shape
        assert np.isin(predicted, [0, 1]).all() and np.isfinite(probability).all()
        assert ((probability >= 0) & (probability <= 1)).all()
        if seed == 42:
            with np.load(audit.ROOT / f'results/predictions/RF_{protocol}_{variant}.npz', allow_pickle=False) as baseline:
                assert np.array_equal(baseline['test_index'], test)
                assert np.array_equal(baseline['actual'], actual[test])
                assert np.array_equal(baseline['predicted'], predicted), 'Seed-42 baseline mismatch; stop before interpreting the new cases.'
            print(f'PASS BASELINE {protocol} {variant}: seed 42 labels match', flush=True)
        metrics = audit.metrics(actual[test], predicted)
        rows.append({'seed': seed, 'protocol': protocol, 'variant': variant,
                     **metrics, 'attack_probability_median': float(np.median(probability[actual[test] == 1]))})
        pd.DataFrame(rows).to_csv(output / 'cases.csv', index=False)
        print(f'DONE {number:02d}/{len(cases):02d} {protocol} {variant} seed={seed}: '
              f'F1={metrics["f1"]:.6f} FP={metrics["FP"]} TP={metrics["TP"]} '
              f'({origin}, {time.perf_counter()-start:.1f}s)', flush=True)
    data = pd.DataFrame(rows)
    summary = []
    for (protocol, variant), subset in data.groupby(['protocol', 'variant'], sort=False):
        summary.append({'protocol': protocol, 'variant': variant, 'seeds': len(subset),
                        'f1_min': float(subset.f1.min()), 'f1_median': float(subset.f1.median()),
                        'f1_max': float(subset.f1.max()), 'f1_mean': float(subset.f1.mean()),
                        'fpr_min': float(subset.fpr.min()), 'fpr_max': float(subset.fpr.max()),
                        'recall_min': float(subset.recall.min()), 'recall_max': float(subset.recall.max())})
    pd.DataFrame(summary).to_csv(output / 'summary.csv', index=False)
    if not smoke:
        paired = data.pivot(index=['seed', 'protocol'], columns='variant', values='f1').reset_index()
        paired['full_minus_no_domain_f1'] = paired['FULL'] - paired['NO_DOMAIN']
        paired.to_csv(output / 'paired_differences.csv', index=False)
    write_json(output / 'status.json', {'mode': plan['mode'], 'plan_sha256': plan_hash,
               'expected_cases': len(cases), 'completed_cases': len(rows),
               'full_experiment_complete': not smoke and len(rows) == 30,
               'finished_at_utc': datetime.now(timezone.utc).isoformat()})
    print('\n' + pd.DataFrame(summary).to_string(index=False), flush=True)
    print('COMPLETE: ' + ('smoke validation only' if smoke else 'all 30 planned cases; no best-seed selection'), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=audit.ROOT / 'results/paper_rf_seeds')
    parser.add_argument('--resume', action='store_true', help='Validate and reuse completed cases under the identical plan and environment.')
    parser.add_argument('--plan-only', action='store_true', help='Save the fixed plan without fitting models.')
    parser.add_argument('--smoke-test', action='store_true', help='Validate only the known seed-42 GROUP-2 FULL case; not the full experiment.')
    args = parser.parse_args()
    main(args.output.resolve(), args.resume, args.plan_only, args.smoke_test)
