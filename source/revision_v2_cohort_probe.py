#!/usr/bin/env python3
"""Post-hoc G2 input sensitivity; substituted scores are not detector results."""
import numpy as np
import pandas as pd

import audit_pipeline as audit
from revision_v2_diagnostics import pipeline, save_npz


def main():
    out = audit.ROOT / 'results/revision_v2'
    df, y, groups = audit.read_data()
    x = audit.inputs(df)
    train, test = [(tr, te) for name, tr, te in audit.load_splits(df, y, groups) if name == 'GROUP_2'][0]
    medians = x.loc[train[y[train] == 1], audit.DOMAIN].median().fillna(0)
    observed = x.loc[test].copy()
    substituted = observed.copy()
    substituted.loc[:, audit.DOMAIN] = medians.to_numpy()
    rows = []
    for model in ['RF', 'LR']:
        cols = audit.feature_sets(x, train, model)['FULL']
        clf = pipeline(model).fit(x.loc[train, cols], y[train])
        baseline = clf.predict(observed[cols])
        with np.load(audit.ROOT / f'results/predictions/{model}_GROUP_2_FULL.npz', allow_pickle=False) as saved:
            assert np.array_equal(baseline, saved['predicted'])
        stored = {'test_index': test, 'actual': y[test]}
        for treatment, values in [('observed', observed), ('name_family_train_attack_medians', substituted)]:
            prob = clf.predict_proba(values[cols])[:, 1]
            stored[treatment] = prob
            for label in [0, 1]:
                selected = prob[y[test] == label]
                rows.append(dict(model=model, treatment=treatment, actual_class=label,
                                 rows=len(selected), mean_probability=float(selected.mean()),
                                 median_probability=float(np.median(selected)),
                                 fraction_above_half=float((selected >= .5).mean())))
        save_npz(out / f'{model}_GROUP_2_cohort_probe.npz', **stored)
    pd.DataFrame(rows).to_csv(out / 'cohort_input_sensitivity.csv', index=False)
    audit.save_json(out / 'cohort_probe_metadata.json', {
        'protocol': 'GROUP_2 frozen indices', 'baseline_predictions_match_vm': True,
        'replacement_features': audit.DOMAIN,
        'replacement_values': {k: float(v) for k, v in medians.items()},
        'scope': 'Post-hoc score sensitivity under a fixed, artificial name-family substitution using training attack medians. The same replacement is applied to every test row; no test label selects replacement values. These are not new detector performance estimates or a causal traffic intervention.',
        'source_sha256': audit.sha256(__file__), 'environment': audit.environment(),
    })
    print(pd.DataFrame(rows).to_string(index=False), flush=True)


if __name__ == '__main__':
    main()
