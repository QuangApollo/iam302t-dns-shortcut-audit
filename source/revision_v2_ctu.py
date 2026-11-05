#!/usr/bin/env python3
"""Verify released CTU representations and test whether dropping DOTS repairs them."""
import argparse
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

import audit_pipeline as audit
import ctu_audit as ctu

OUT = audit.ROOT / 'results/revision_v2'


def save_npz(path, **arrays):
    buffer = io.BytesIO()
    np.savez_compressed(buffer, **arrays)
    path.write_bytes(buffer.getvalue())


def main(originals):
    OUT.mkdir(exist_ok=True)
    metadata = json.loads((audit.ROOT / 'results/ctu_preparation.json').read_text())
    source_profiles = []
    for split in ['train', 'test']:
        path = originals / f'{split}_combined_multiclass.csv.gz'
        raw = path.read_bytes()
        assert hashlib.md5(raw).hexdigest() == metadata[split]['publisher_md5']
        assert hashlib.sha256(raw).hexdigest() == metadata[split]['source_sha256']
        groups = {label: dict(rows=0, with_dot=0, prefix45_with_dot=0, longer_than45=0) for label in ['0', '1', '2']}
        with gzip.open(path, 'rt', newline='') as stream:
            for row in csv.DictReader(stream):
                text = row['domain']
                stats = groups[row['class']]
                stats['rows'] += 1
                stats['with_dot'] += int('.' in text)
                stats['prefix45_with_dot'] += int('.' in text[:45])
                stats['longer_than45'] += int(len(text) > 45)
        for label, values in groups.items():
            assert values['rows'] == metadata[split]['original_label_counts'][label]
            source_profiles.append(dict(split=split, label=int(label), **values))
    pd.DataFrame(source_profiles).to_csv(OUT / 'ctu_original_representation.csv', index=False)

    train, yt = ctu.load('train')
    test, y = ctu.load('test')
    xtr = np.asarray([ctu.features(s) for s in train], dtype=np.float32)
    xfull = np.asarray([ctu.features(s) for s in test], dtype=np.float32)
    xfirst = np.asarray([ctu.features(s.split('.', 1)[0]) for s in test], dtype=np.float32)
    names = ['length', 'dots', 'max_label_length', 'mean_label_length', 'digit_fraction',
             'hyphen_fraction', 'entropy', 'unique_character_fraction']
    scores, coefficients, predicted_by_case = [], [], {}
    saved = pd.read_csv(audit.ROOT / 'results/ctu_results.csv')
    for model, columns in [('LR8', list(range(8))), ('LR7_NO_DOTS', [i for i in range(8) if i != 1])]:
        clf = Pipeline([('scale', StandardScaler()), ('model', LogisticRegression(
                       C=.5, class_weight='balanced', max_iter=2000, random_state=42))])
        clf.fit(xtr[:, columns], yt)
        for column, coefficient in zip(columns, clf.named_steps['model'].coef_[0]):
            coefficients.append(dict(model=model, feature=names[column], coefficient=float(coefficient)))
        for representation, x in [('FULL_STRING', xfull), ('FIRST_LABEL', xfirst)]:
            pred = clf.predict(x[:, columns]).astype(np.int8)
            metrics = audit.metrics(y, pred)
            if model == 'LR8':
                original = saved[(saved.model == 'LR8') & (saved.representation == representation)].iloc[0]
                for key, value in metrics.items():
                    assert abs(original[key] - value) < 1e-10, (model, representation, key)
            case = model + '_' + representation
            predicted_by_case[case] = pred
            scores.append(dict(model=model, representation=representation, **metrics))
            save_npz(OUT / (case + '.npz'), test_index=np.arange(len(y), dtype=np.int32),
                     actual=y, predicted=pred)
            print('PASS CTU', case, 'F1=', metrics['f1'], 'FP=', metrics['FP'], flush=True)
    differences = {representation: int((predicted_by_case['LR8_' + representation] !=
                   predicted_by_case['LR7_NO_DOTS_' + representation]).sum())
                   for representation in ['FULL_STRING', 'FIRST_LABEL']}
    dot_coefficient = [x['coefficient'] for x in coefficients if x['model'] == 'LR8' and x['feature'] == 'dots'][0]
    assert abs(dot_coefficient) < 1e-12
    equal_train = (xtr[:, 0] == xtr[:, 2]) & (xtr[:, 0] == xtr[:, 3])
    equal_test = (xfull[:, 0] == xfull[:, 2]) & (xfull[:, 0] == xfull[:, 3])
    pd.DataFrame(scores).to_csv(OUT / 'ctu_no_dots_control.csv', index=False)
    pd.DataFrame(coefficients).to_csv(OUT / 'ctu_lr_coefficients.csv', index=False)
    audit.save_json(OUT / 'ctu_control_metadata.json', {
        'environment': audit.environment(), 'original_md5_verified': True,
        'original_sha256_verified': True, 'core_lr8_metrics_reproduced': True,
        'lr8_dot_coefficient': dot_coefficient, 'prediction_differences_after_dropping_dots': differences,
        'train_length_equals_max_and_mean_label_length': int(equal_train.sum()),
        'train_rows': len(train), 'test_rows_violating_training_length_identity': int((~equal_test).sum()),
        'test_rows': len(test), 'test_attack': int(y.sum()),
        'prefix45_scope': 'Exposure check under post-truncation to 45 characters, as in the associated deepseq default. Not a replay of the authors exact trained checkpoint.',
        'first_label_scope': 'Lossy test-input sensitivity; not a reconstruction of original registrable domains or a validated repair.',
        'source_sha256': audit.sha256(__file__),
    })
    print('DROP DOTS differences', differences, 'DOTS coefficient', dot_coefficient, flush=True)
    print(pd.DataFrame(source_profiles).to_string(index=False), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--originals', type=Path, required=True)
    main(parser.parse_args().originals)
