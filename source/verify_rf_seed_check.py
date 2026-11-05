#!/usr/bin/env python3
"""Independently check all saved RF-seed evidence, without fitting models.

Counts are derived directly from CSV labels and NPZ predictions. This verifier
does not call the experiment's metric or training functions. Original VM files
and logs are read only; a separate verification receipt is written.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import tarfile

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SEEDS = [42, 0, 1, 7, 2026]
PROTOCOLS = ['GROUP_1', 'GROUP_2', 'GROUP_3']
VARIANTS = ['FULL', 'NO_DOMAIN']


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def derived_metrics(actual, predicted):
    tn, fp, fn, tp = map(int, np.bincount(2 * actual + predicted, minlength=4))
    return {'TN': tn, 'FP': fp, 'FN': fn, 'TP': tp,
            'accuracy': (tn + tp) / len(actual),
            'precision': tp / (tp + fp) if tp + fp else 0.,
            'recall': tp / (tp + fn),
            'f1': 2 * tp / (2 * tp + fp + fn),
            'fpr': fp / (tn + fp)}


def compare(row, expected):
    for key, value in expected.items():
        assert abs(float(row[key]) - value) < 1e-12, (key, row[key], value)


def main(root, check_received_archive):
    result = root / 'results/paper_rf_seeds'
    plan = json.loads((result / 'plan.json').read_text())
    fixed_plan = json.loads((root / 'docs/experiment_plans/rf_seed_plan.json').read_text())
    assert plan == fixed_plan, 'Received plan differs from the plan fixed before fitting.'
    assert plan['mode'] == 'full' and plan['expected_cases'] == 30
    assert plan['seeds'] == SEEDS and plan['protocols'] == PROTOCOLS
    assert plan['variants'] == VARIANTS
    grid = [(s, p, v) for s in SEEDS for p in PROTOCOLS for v in VARIANTS]
    assert plan['cases'] == [{'seed': s, 'protocol': p, 'variant': v} for s, p, v in grid]
    plan_hash = hashlib.sha256(json.dumps(plan, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    for key, path in [
        ('dataset_sha256', 'data/cic/CIC-Bell-DNS-EXF-2021.csv'),
        ('split_sha256', 'splits/frozen_splits.npz'),
        ('source_sha256', 'source/paper_rf_seed_check.py'),
        ('pipeline_source_sha256', 'source/revision_v2_diagnostics.py'),
        ('audit_source_sha256', 'source/audit_pipeline.py')]:
        assert sha256(root / path) == plan[key], (key, path)
    status = json.loads((result / 'status.json').read_text())
    assert status['mode'] == 'full' and status['plan_sha256'] == plan_hash
    assert status['full_experiment_complete'] is True
    assert status['expected_cases'] == status['completed_cases'] == 30
    metadata = json.loads((result / 'run_metadata.json').read_text())
    assert metadata['plan_sha256'] == plan_hash
    previous_vm = json.loads((root / 'results/PAPER_VM_RECEIPT_VALIDATION.json').read_text())['vm_environment']
    for key, value in metadata['environment'].items():
        if key == 'python':
            assert value == previous_vm['python'].split()[0]
        elif key == 'platform':
            assert value == previous_vm['platform']
        elif key not in ['seed', 'dataset_sha256']:
            assert value == previous_vm['packages'][key], key
    frame = pd.read_csv(root / 'data/cic/CIC-Bell-DNS-EXF-2021.csv', usecols=['label', 'sld'])
    assert len(frame) == 228042 and set(frame.label) == {'heavy_benign', 'heavy_attack'}
    actual = frame.label.map({'heavy_benign': 0, 'heavy_attack': 1}).to_numpy(np.int8)
    groups = frame.sld.fillna('MISSING_SLD').astype(str).str.lower().str.strip().replace('', 'MISSING_SLD').to_numpy()
    csv = pd.read_csv(result / 'cases.csv')
    assert list(zip(csv.seed, csv.protocol, csv.variant)) == grid
    wanted = {f'RF_{p}_{v}_seed_{s}.npz' for s, p, v in grid}
    assert {p.name for p in result.glob('*.npz')} == wanted
    log_path = result / 'execution.log'
    log = log_path.read_text()
    original_log = root / 'logs/paper_vm/08_rf_seeds.log'
    if original_log.exists():
        assert original_log.read_bytes() == log_path.read_bytes()
    assert len(re.findall(r'^DONE \d+/30 ', log, flags=re.M)) == 30
    assert len(re.findall(r'^PASS BASELINE ', log, flags=re.M)) == 6
    assert len(re.findall(r'\(fitted, ', log)) == 30
    assert 'COMPLETE: all 30 planned cases; no best-seed selection' in log
    calculated, array_hashes, baselines = [], {}, []
    with np.load(root / 'splits/frozen_splits.npz', allow_pickle=False) as splits:
        for number, (seed, protocol, variant) in enumerate(grid):
            train = splits[protocol + '_train']
            test = splits[protocol + '_test']
            assert len(np.unique(test)) == len(test)
            assert len(np.unique(train)) == len(train)
            assert len(train) + len(test) == len(actual)
            assert len(np.intersect1d(train, test)) == 0
            assert not set(groups[train]) & set(groups[test])
            path = result / f'RF_{protocol}_{variant}_seed_{seed}.npz'
            with np.load(path, allow_pickle=False) as saved:
                assert str(saved['plan_sha256']) == plan_hash
                assert int(saved['seed']) == seed
                assert str(saved['protocol']) == protocol and str(saved['variant']) == variant
                assert np.array_equal(saved['test_index'], test)
                assert np.array_equal(saved['actual'], actual[test])
                predicted = saved['predicted']
                probability = saved['attack_probability']
                assert predicted.shape == probability.shape == actual[test].shape
                assert np.isin(predicted, [0, 1]).all()
                assert np.isfinite(probability).all() and ((probability >= 0) & (probability <= 1)).all()
                # sklearn's binary argmax selects class 0 for an exact 0.5 tie.
                assert np.array_equal(predicted, (probability > .5).astype(np.int8))
                values = derived_metrics(actual[test], predicted)
                values['attack_probability_median'] = float(np.median(probability[actual[test] == 1]))
                compare(csv.iloc[number], values)
                if seed == 42:
                    with np.load(root / f'results/predictions/RF_{protocol}_{variant}.npz', allow_pickle=False) as baseline:
                        for key in ['test_index', 'actual', 'predicted']:
                            assert np.array_equal(saved[key], baseline[key]), (path.name, key)
                    baselines.append(f'{protocol}/{variant}')
            array_hashes[path.name] = sha256(path)
            calculated.append({'seed': seed, 'protocol': protocol, 'variant': variant, **values})
    data = pd.DataFrame(calculated)
    summary = pd.read_csv(result / 'summary.csv')
    assert len(summary) == 6 and not summary.duplicated(['protocol', 'variant']).any()
    for (protocol, variant), subset in data.groupby(['protocol', 'variant']):
        row = summary[(summary.protocol == protocol) & (summary.variant == variant)].iloc[0]
        compare(row, {'seeds': 5, 'f1_min': subset.f1.min(), 'f1_median': subset.f1.median(),
                     'f1_max': subset.f1.max(), 'f1_mean': subset.f1.mean(),
                     'fpr_min': subset.fpr.min(), 'fpr_max': subset.fpr.max(),
                     'recall_min': subset.recall.min(), 'recall_max': subset.recall.max()})
    paired = pd.read_csv(result / 'paired_differences.csv')
    assert len(paired) == 15 and not paired.duplicated(['seed', 'protocol']).any()
    direction = {}
    for _, row in paired.iterrows():
        subset = data[(data.seed == row.seed) & (data.protocol == row.protocol)]
        full = float(subset[subset.variant == 'FULL'].iloc[0].f1)
        removed = float(subset[subset.variant == 'NO_DOMAIN'].iloc[0].f1)
        compare(row, {'FULL': full, 'NO_DOMAIN': removed, 'full_minus_no_domain_f1': full - removed})
        direction.setdefault(row.protocol, []).append(int(np.sign(full - removed)))
    assert direction == {'GROUP_1': [1] * 5, 'GROUP_2': [-1] * 5, 'GROUP_3': [1] * 5}
    archive = root / 'evidence/IAM302t_RF_Seeds_20261104.tar.gz'
    if check_received_archive:
        assert archive.exists(), 'Received archive is available in the complete source package.'
        with tarfile.open(archive, 'r:gz') as received:
            for member in received.getmembers():
                name = Path(member.name)
                assert not name.is_absolute() and '..' not in name.parts
                assert member.isdir() or member.isfile()
                if member.isfile():
                    assert received.extractfile(member).read() == (root / name).read_bytes(), member.name
    receipt = {
        'verified_at_utc': datetime.now(timezone.utc).isoformat(),
        'plan_sha256': plan_hash, 'received_archive_sha256': sha256(archive) if archive.exists() else None,
        'received_archive_bytes_checked': check_received_archive,
        'all_checks_passed': True, 'cases_recomputed': 30, 'summaries_recomputed': 6,
        'paired_differences_recomputed': 15, 'seed42_baselines_equal': baselines,
        'source_and_dataset_and_split_bindings': True,
        'vm_environment_matches_previous_receipt': True,
        'label_probability_consistency': True,
        'f1_difference_signs_by_protocol': direction,
        'prediction_file_sha256': array_hashes,
        'verifier_sha256': sha256(__file__),
        'scope': 'Saved-evidence verification without refitting. Seeds measure stochastic-estimator sensitivity on fixed rows; they are not independent traffic samples or confidence intervals.'}
    (result / 'verification.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print('PASS: 30 per-row arrays, confusion matrices and metrics against original CSV labels')
    print('PASS: six seed-42 baselines and six min/median/max summaries')
    print('PASS: 15 paired differences; fold-specific direction preserved at every seed')
    print('PASS: pre-fixed plan, source/data/split hashes and VM environment')
    if check_received_archive:
        print('PASS: original received archive matches every retained member byte for byte')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--check-received-archive', action='store_true',
                        help='Also bind all original received members to the immutable VM archive; use before rerunning fits.')
    args = parser.parse_args()
    main(args.root.resolve(), args.check_received_archive)
