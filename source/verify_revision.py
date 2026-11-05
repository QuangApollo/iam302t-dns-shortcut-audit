#!/usr/bin/env python3
"""Recompute saved core and revision evidence without refitting or changing VM logs."""
import json
import numpy as np
import pandas as pd

import audit_pipeline as audit
import ctu_audit as ctu


def equal_metrics(row, expected):
    for name, value in expected.items():
        assert abs(float(row[name]) - value) < 1e-9, (name, row[name], value)


def main():
    checks = []
    df, y, groups = audit.read_data()
    splits = {name: (train, test) for name, train, test in audit.load_splits(df, y, groups)}
    for model in ['LR', 'RF']:
        cases = pd.read_csv(audit.ROOT / f'results/{model.lower()}_results.csv')
        assert len(cases) == 25
        for _, case in cases.iterrows():
            with np.load(audit.ROOT / f'results/predictions/{model}_{case.protocol}_{case.variant}.npz', allow_pickle=False) as saved:
                assert np.array_equal(saved['test_index'], splits[case.protocol][1])
                assert np.array_equal(saved['actual'], y[saved['test_index']])
                equal_metrics(case, audit.metrics(saved['actual'], saved['predicted']))
        checks.append(f'PASS {model}: all 25 core prediction arrays and metrics')
    out = audit.ROOT / 'results/revision_v2'
    refits = pd.read_csv(out / 'refit_cases.csv')
    assert len(refits) == 8
    for _, case in refits.iterrows():
        stem = f'{case.model}_{case.protocol}_{case.variant}'
        with np.load(out / (stem + '_scores.npz'), allow_pickle=False) as revised, np.load(audit.ROOT / 'results/predictions' / (stem + '.npz'), allow_pickle=False) as vm:
            for key in ['test_index', 'actual', 'predicted']:
                assert np.array_equal(revised[key], vm[key]), (stem, key)
            assert np.isfinite(revised['attack_probability']).all()
            equal_metrics(case, audit.metrics(revised['actual'], revised['predicted']))
    checks.append('PASS eight mechanism refits match original VM predictions exactly')
    cohort = pd.read_csv(out / 'cohort_input_sensitivity.csv')
    for model in ['RF', 'LR']:
        with np.load(out / f'{model}_GROUP_2_cohort_probe.npz', allow_pickle=False) as saved:
            assert np.array_equal(saved['test_index'], splits['GROUP_2'][1])
            assert np.array_equal(saved['actual'], y[saved['test_index']])
            for treatment in ['observed', 'name_family_train_attack_medians']:
                for label in [0, 1]:
                    p = saved[treatment][saved['actual'] == label]
                    row = cohort[(cohort.model == model) & (cohort.treatment == treatment) & (cohort.actual_class == label)].iloc[0]
                    assert len(p) == row.rows
                    for name, value in [('mean_probability', p.mean()), ('median_probability', np.median(p)), ('fraction_above_half', (p >= .5).mean())]:
                        assert abs(float(row[name]) - value) < 1e-12
    checks.append('PASS all eight cohort summaries recomputed from saved per-row scores')
    x = audit.inputs(df)
    assert 'sld' not in x
    assert audit.inputs(df.assign(sld='INERT_GROUP_TOKEN')).equals(x)
    mechanism = json.loads((out / 'mechanism.json').read_text())
    components = pd.read_csv(out / 'rf_group2_path_contributions.csv')
    reconstructed = mechanism['path_decomposition_baseline'] + components.contribution.sum()
    assert abs(reconstructed - mechanism['rf_direct_probability']) < 1e-10
    checks.append('PASS grouping-only sld negative control and additive RF path score')
    _, actual = ctu.load('test')
    cases = pd.read_csv(out / 'ctu_no_dots_control.csv')
    assert len(cases) == 4
    predictions = {}
    for _, case in cases.iterrows():
        stem = case.model + '_' + case.representation
        with np.load(out / (stem + '.npz'), allow_pickle=False) as saved:
            assert np.array_equal(saved['test_index'], np.arange(len(actual)))
            assert np.array_equal(saved['actual'], actual)
            equal_metrics(case, audit.metrics(actual, saved['predicted']))
            predictions[stem] = saved['predicted']
    for representation in ['FULL_STRING', 'FIRST_LABEL']:
        assert np.array_equal(predictions['LR8_' + representation], predictions['LR7_NO_DOTS_' + representation])
    checks.append('PASS four CTU confusion matrices and unchanged predictions after deleting DOTS')
    metadata = json.loads((audit.ROOT / 'results/ctu_preparation.json').read_text())
    for split in ['train', 'test']:
        assert audit.sha256(audit.ROOT / f'data/ctu/binary/{split}_binary.csv.gz') == metadata[split]['binary_sha256']
    checks.append('PASS dataset/split bindings, coarse-token disjointness, and CTU binary hashes')
    audit.save_json(out / 'verification.json', {'checks': checks, 'environment': audit.environment(),
                    'scope': 'Saved numerical evidence verification without model refitting; original VM receipt/logs are retained unchanged.',
                    'source_sha256': audit.sha256(__file__)})
    print('\n'.join(checks))


if __name__ == '__main__':
    main()
