#!/usr/bin/env python3
"""Reproduce frozen G1/G2 cases and inspect the actual RF input mechanism."""
import io
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

import audit_pipeline as audit

ROOT = audit.ROOT
OUT = ROOT / 'results/revision_v2'


def save_npz(path, **arrays):
    buffer = io.BytesIO()
    np.savez_compressed(buffer, **arrays)
    path.write_bytes(buffer.getvalue())


def pipeline(model):
    steps = [('fill', SimpleImputer(strategy='constant', fill_value=0,
                                    keep_empty_features=True))]
    if model == 'RF':
        steps.append(('model', RandomForestClassifier(n_estimators=100, max_depth=16,
                      min_samples_leaf=2, random_state=42, n_jobs=2)))
    else:
        steps += [('scale', StandardScaler()), ('model', LogisticRegression(
                  C=.5, class_weight='balanced', max_iter=2000, random_state=42))]
    return Pipeline(steps)


def tree_path_components(forest, vector, columns):
    baseline, delta = 0., np.zeros(len(columns))
    paths = []
    for estimator in forest.estimators_:
        tree = estimator.tree_
        value = tree.value[:, 0, :]
        positive = value[:, 1] / value.sum(axis=1)
        baseline += positive[0]
        node, path = 0, []
        while tree.children_left[node] != tree.children_right[node]:
            feature, threshold = int(tree.feature[node]), float(tree.threshold[node])
            left = bool(vector[feature] <= threshold)
            child = int(tree.children_left[node] if left else tree.children_right[node])
            contribution = float(positive[child] - positive[node])
            delta[feature] += contribution
            path.append(dict(feature=columns[feature], value=float(vector[feature]),
                             threshold=threshold, direction='le' if left else 'gt',
                             contribution=contribution))
            node = child
        paths.append(dict(leaf_probability=float(positive[node]), path=path))
    n = len(forest.estimators_)
    return float(baseline / n), delta / n, paths


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    df, labels, group = audit.read_data()
    x = audit.inputs(df)
    assert 'sld' not in x and 'longest_word' not in x
    # Split IDs are kept fixed: modifying the group field cannot change model inputs.
    assert audit.inputs(df.assign(sld='GROUP_FIELD_NOT_A_MODEL_INPUT')).equals(x)
    split = {name: (train, test) for name, train, test in audit.load_splits(df, labels, group)}
    models, rows, group_rows = {}, [], []
    for name in ['GROUP_1', 'GROUP_2']:
        train, test = split[name]
        for model in ['RF', 'LR']:
            sets = audit.feature_sets(x, train, model)
            for variant in ['FULL', 'NO_DOMAIN']:
                columns = sets[variant]
                clf = pipeline(model).fit(x.loc[train, columns], labels[train])
                predicted = clf.predict(x.loc[test, columns])
                probability = clf.predict_proba(x.loc[test, columns])[:, 1]
                with np.load(ROOT / f'results/predictions/{model}_{name}_{variant}.npz', allow_pickle=False) as saved:
                    assert np.array_equal(saved['test_index'], test)
                    assert np.array_equal(saved['actual'], labels[test])
                    assert np.array_equal(saved['predicted'], predicted), 'Refit did not match frozen evidence'
                key = (name, model, variant)
                models[key] = (clf, columns)
                row = dict(protocol=name, model=model, variant=variant,
                           **audit.metrics(labels[test], predicted))
                row['attack_probability_median'] = float(np.median(probability[labels[test] == 1]))
                row['attack_probability_q10'] = float(np.quantile(probability[labels[test] == 1], .1))
                row['attack_probability_q90'] = float(np.quantile(probability[labels[test] == 1], .9))
                rows.append(row)
                save_npz(OUT / f'{model}_{name}_{variant}_scores.npz', test_index=test,
                         actual=labels[test], predicted=predicted.astype(np.int8),
                         attack_probability=probability.astype(np.float32))
                for token in ['192', '224']:
                    mask = group[test] == token
                    if mask.any():
                        group_rows.append(dict(protocol=name, model=model, variant=variant,
                            token=token, rows=int(mask.sum()), **audit.metrics(labels[test][mask], predicted[mask])))
                print(f'PASS REFIT {model} {name} {variant}: TP={row["TP"]} F1={row["f1"]:.6f}', flush=True)
    pd.DataFrame(rows).to_csv(OUT / 'refit_cases.csv', index=False)
    pd.DataFrame(group_rows).to_csv(OUT / 'dominant_token_cases.csv', index=False)

    train, test = split['GROUP_2']
    rf, columns = models[('GROUP_2', 'RF', 'FULL')]
    pred = rf.predict(x.loc[test, columns])
    failed = test[(labels[test] == 1) & (pred == 0)]
    filled = rf.named_steps['fill'].transform(x.loc[failed, columns])
    unique, inverse, counts = np.unique(filled, axis=0, return_inverse=True, return_counts=True)
    largest = int(np.argmax(counts))
    representative = int(failed[np.flatnonzero(inverse == largest)[0]])
    vector = unique[largest]
    base, contribution, paths = tree_path_components(rf.named_steps['model'], vector, columns)
    direct = float(rf.predict_proba(x.loc[[representative], columns])[0, 1])
    assert abs(base + contribution.sum() - direct) < 1e-10
    parts = pd.DataFrame({'feature': columns, 'contribution': contribution})
    parts['family'] = parts.feature.map(lambda f: 'name_statistics' if f in audit.DOMAIN else
                                        'record_type' if f.endswith('_frequency') or f.startswith('raw_type_') else 'other')
    parts.to_csv(OUT / 'rf_group2_path_contributions.csv', index=False)

    # Post-hoc model-input sensitivity, not a new evaluation score or a traffic intervention.
    training_attack = train[labels[train] == 1]
    medians = x.loc[training_attack, audit.DOMAIN].median().fillna(0)
    original = x.loc[[representative]].copy()
    substituted = original.copy()
    substituted.loc[:, audit.DOMAIN] = medians.to_numpy()
    probes = []
    for model in ['RF', 'LR']:
        clf, cols = models[('GROUP_2', model, 'FULL')]
        for treatment, values in [('observed', original), ('name_family_train_attack_medians', substituted)]:
            probes.append(dict(model=model, treatment=treatment,
                          attack_probability=float(clf.predict_proba(values[cols])[0, 1]),
                          predicted=int(clf.predict(values[cols])[0])))
    pd.DataFrame(probes).to_csv(OUT / 'representative_input_sensitivity.csv', index=False)

    shifts = []
    for name in ['GROUP_1', 'GROUP_2']:
        tr, te = split[name]
        for family, index in [('train_attack', tr[labels[tr] == 1]), ('test_attack', te[labels[te] == 1])]:
            for column in audit.DOMAIN + audit.OTHER:
                values = x.loc[index, column].fillna(0)
                shifts.append(dict(protocol=name, population=family, feature=column,
                                   minimum=float(values.min()), median=float(values.median()),
                                   maximum=float(values.max()), q10=float(values.quantile(.1)),
                                   q90=float(values.quantile(.9))))
    pd.DataFrame(shifts).to_csv(OUT / 'feature_shift_profiles.csv', index=False)
    audit.save_json(OUT / 'mechanism.json', {
        'environment': audit.environment(), 'refit_cases': len(rows),
        'all_refit_predictions_match_saved_vm': True,
        'model_input_columns': {'RF_FULL': columns, 'grouping_only': ['sld']},
        'literal_sld_input_negative_control': 'PASS: replacing sld while retaining frozen indices leaves every model input unchanged',
        'representative_original_row': representative, 'representative_token': str(group[representative]),
        'dominant_false_negative_pattern_rows': int(counts[largest]), 'group2_false_negatives': len(failed),
        'representative_inputs': {c: float(v) for c, v in zip(columns, vector)},
        'path_decomposition_baseline': base, 'path_decomposition_probability': base + float(contribution.sum()),
        'rf_direct_probability': direct, 'per_tree_paths': paths,
        'path_decomposition_scope': 'Order-dependent exact tree-path score decomposition, not causal attribution or Shapley values',
        'input_substitution_scope': 'Post-hoc sensitivity of one common observed false-negative vector; training attack medians replace the 14 name-statistic inputs. It is not a valid traffic transformation or an independently tested detector.',
    })
    print('REPRESENTATIVE', representative, 'pattern rows', int(counts[largest]), 'RF p=', direct, flush=True)
    print(parts.reindex(parts.contribution.abs().sort_values(ascending=False).index).head(8).to_string(index=False), flush=True)
    print(pd.DataFrame(probes).to_string(index=False), flush=True)


if __name__ == '__main__':
    main()
