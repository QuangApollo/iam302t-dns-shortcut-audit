#!/usr/bin/env python3
"""Build revised report tables, numbers and figures directly from measured CSVs."""
import json
import io
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'report'
TABLES = OUT / 'tables'
TABLES.mkdir(exist_ok=True)
FIGURES = OUT / 'figures'
VARIANTS = ['FULL', 'NO_QTYPE', 'NO_DOMAIN', 'NO_BOTH', 'NO_QTYPE_TTL', 'NO_BOTH_TTL']
LABELS = {'FULL': 'Full', 'NO_QTYPE': 'No type', 'NO_DOMAIN': 'No domain',
          'NO_BOTH': 'Neither', 'NO_QTYPE_TTL': 'No type/TTL', 'NO_BOTH_TTL': 'Neither/TTL'}


def fmt(x):
    return f'{int(x):,}'


def table(name, specification, header, rows, size=r'\footnotesize'):
    lines = [r'\centering' + size,
             r'\begin{tabular}{@{}' + specification + r'@{}}',
             r'\toprule', ' & '.join(header) + r'\\\midrule']
    lines += [' & '.join(map(str, row)) + r'\\' for row in rows]
    lines += [r'\bottomrule', r'\end{tabular}']
    (TABLES / (name + '.tex')).write_text('\n'.join(lines) + '\n')


def main():
    rf = pd.read_csv(ROOT / 'results/rf_results.csv')
    lr = pd.read_csv(ROOT / 'results/lr_results.csv')
    inventory = pd.read_csv(ROOT / 'results/split_inventory.csv')
    proxy = pd.read_csv(ROOT / 'results/qtype_proxy_results.csv')
    ref = pd.read_csv(ROOT / 'results/reference_inventory_results.csv')
    ctu = pd.read_csv(ROOT / 'results/ctu_results.csv')
    audit = json.loads((ROOT / 'results/dataset_audit.json').read_text())
    overlap = pd.read_csv(ROOT / 'results/vector_overlap.csv')
    repeated_row_test = int(overlap[overlap.protocol == 'ROW'].iloc[0].test_rows_matching_train_nonlabel_vector)
    summary_rows = []
    for model, data in [('LR', lr), ('RF', rf)]:
        for v in VARIANTS:
            a = data[(data.variant == v) & data.protocol.str.startswith('GROUP_')].sort_values('protocol')
            row = data[(data.variant == v) & (data.protocol == 'ROW')].iloc[0]
            tn, fp, fn, tp = (int(a[c].sum()) for c in ['TN', 'FP', 'FN', 'TP'])
            pooled = 2 * tp / (2 * tp + fp + fn)
            summary_rows.append({'model': model, 'variant': v, 'row_f1': row.f1,
                                 'row_fpr': row.fpr, 'group1_f1': a.iloc[0].f1,
                                 'group2_f1': a.iloc[1].f1, 'group3_f1': a.iloc[2].f1,
                                 'mean_f1': a.f1.mean(), 'sd_f1': a.f1.std(),
                                 'pooled_f1': pooled})
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(ROOT / 'results/model_summary.csv', index=False)
    rows = []
    for _, r in summary.iterrows():
        rows.append([r.model, LABELS[r.variant], f'{r.row_f1:.4f}', f'{100*r.row_fpr:.2f}',
                     f'{r.group1_f1:.4f}', f'{r.group2_f1:.4f}', f'{r.group3_f1:.4f}',
                     f'{r.mean_f1:.4f}', f'{r.sd_f1:.4f}', f'{r.pooled_f1:.4f}'])
    table('model_results', 'llrrrrrrrr',
          ['Model', 'Feature set', 'Row F1', 'Row FPR\\%', 'G1 F1', 'G2 F1', 'G3 F1',
           'Mean F1', 'SD', 'Pooled F1'], rows)
    table('splits', 'lrrrrrr',
          ['Protocol', 'Train', 'Test', 'Test benign', 'Test attack', 'Shared SLD', 'Shared vectors'],
          [[r.protocol.replace('_', ' '), fmt(r.train_n), fmt(r.test_n),
            fmt(r.test_benign), fmt(r.test_attack), fmt(r.shared_sld),
            fmt(r.shared_complete_nonlabel_vectors)] for _, r in inventory.iterrows()])
    table('data_audit', 'p{4.55cm}r', ['Measurement', 'Count'],
          [['Rows', fmt(audit['n_rows'])],
           ['Duplicate complete rows beyond first', fmt(audit['duplicate_full_rows_beyond_first'])],
           ['Distinct nonlabel vectors', fmt(audit['distinct_nonlabel_vectors'])],
           ['Vectors carrying both labels', fmt(audit['conflicting_nonlabel_vector_groups'])],
           ['Rows in those conflicting vectors', fmt(audit['rows_in_conflicting_vectors'])],
           ['Row-test vectors also observed in train (rows)', fmt(repeated_row_test)]])
    table('proxy', 'lrrrr', ['Inputs for PTR classifier', 'Row', 'G1', 'G2', 'G3'],
          [[label] + [f'{100*proxy[(proxy.protocol == p) & (proxy.features == v)].iloc[0].accuracy:.2f}'
                     for p in ['ROW', 'GROUP_1', 'GROUP_2', 'GROUP_3']]
           for label, v in [('TTL only', 'TTL_ONLY'), ('Other fields', 'OTHER_ONLY'),
                            ('Other without TTL', 'OTHER_WITHOUT_TTL')]])
    table('reference', 'lrrrr', ['Feature set', 'Inputs', 'Accuracy\\%', 'F1', 'FPR\\%'],
          [[LABELS[r.variant], int(r.n_features_before_encoding), f'{100*r.accuracy:.2f}',
            f'{r.f1:.4f}', f'{100*r.fpr:.2f}'] for _, r in ref.iterrows()])
    table('ctu', 'llrrrr', ['Model', 'Test input', 'FP', 'TP', 'F1', 'FPR\\%'],
          [[r.model, 'Full' if r.representation == 'FULL_STRING' else 'First label',
            fmt(r.FP), fmt(r.TP), f'{r.f1:.4f}', f'{100*r.fpr:.2f}']
           for _, r in ctu.iloc[:6].iterrows()])
    table('ctu_structure', 'llrrrr', ['Split', 'Class', 'Rows', 'No dots', '1 dot', '$\\geq2$ dots'],
          [[r['split'], 'Benign' if r.label == 0 else 'Tunnel', fmt(r.rows),
            fmt(r.zero_dots), fmt(r.one_dot), fmt(r.two_plus_dots)]
           for _, r in pd.read_csv(ROOT / 'results/ctu_structure.csv').iterrows()])
    lab = pd.read_csv(ROOT / 'lab/results/02_missing_value_sensitivity.csv')
    rows = []
    for model in ['CTRL_NULL', 'POINT_NO_TYPE', 'GRAPH_NO_TYPE', 'HYBRID_NO_TYPE']:
        for strat, label in [('ORIGINAL_ZERO', 'Zero'), ('TRAIN_MEDIAN', 'Median')]:
            r = lab[(lab.model == model) & (lab.strategy == strat)].iloc[0]
            rows.append([model.replace('_NO_TYPE', '').replace('CTRL_NULL', 'Control'),
                         label, int(r.TN), int(r.FP), int(r.FN), int(r.TP), f'{r.f1:.4f}'])
    table('lab_imputation', 'llrrrrr', ['Features', 'Imputer', 'TN', 'FP', 'FN', 'TP', 'F1'], rows)
    ab = pd.read_csv(ROOT / 'lab/results/03_feature_ablation.csv')
    variants = [('GRAPH_FULL', 'None'),
                ('GRAPH_MINUS_CLIENT_DOMAIN_DEGREE', 'Client--domain degree'),
                ('GRAPH_MINUS_CLIENT_DOMAIN_QUERY_SHARE', 'Domain query share'),
                ('GRAPH_MINUS_DOMAIN_ANSWER_IP_DEGREE', 'Domain--answer-IP degree'),
                ('GRAPH_MINUS_3_PROXIES', 'All three proxies'),
                ('GRAPH_MINUS_3_PROXIES_AND_QNAME_COUNT', 'Three proxies + QNAME count')]
    table('lab_ablation', 'lrrr', ['Removed graph input', 'Kept', 'FP', 'F1'],
          [[label, int(ab[ab.variant == v].iloc[0].n_features),
            int(ab[ab.variant == v].iloc[0].FP), f'{ab[ab.variant == v].iloc[0].f1:.4f}']
           for v, label in variants])
    row_rf = rf[(rf.protocol == 'ROW') & (rf.variant == 'FULL')].iloc[0]
    group_rf = summary[(summary.model == 'RF') & (summary.variant == 'FULL')].iloc[0]
    group_lr = summary[(summary.model == 'LR') & (summary.variant == 'FULL')].iloc[0]
    vector_rf = rf[(rf.protocol == 'EXACT_VECTOR_GROUP') & (rf.variant == 'FULL')].iloc[0]
    ref_full = ref[ref.variant == 'FULL'].iloc[0]
    macros = {'RowRFFOne': f'{row_rf.f1:.4f}', 'RowRFAccuracy': f'{100*row_rf.accuracy:.2f}',
              'RFMean': f'{group_rf.mean_f1:.4f}', 'RFSD': f'{group_rf.sd_f1:.4f}',
              'RFPooled': f'{group_rf.pooled_f1:.4f}', 'LRMean': f'{group_lr.mean_f1:.4f}',
              'LRSD': f'{group_lr.sd_f1:.4f}', 'VectorRFFOne': f'{vector_rf.f1:.4f}',
              'ReferenceAccuracy': f'{100*ref_full.accuracy:.2f}',
              'ReferenceFOne': f'{ref_full.f1:.4f}'}
    (OUT / 'metrics.tex').write_text('\n'.join(
        '\\newcommand{\\' + k + '}{' + v + '}' for k, v in macros.items()) + '\n')
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9,
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'pdf.fonttype': 42})
    protocols = ['ROW', 'GROUP_1', 'GROUP_2', 'GROUP_3', 'EXACT_VECTOR_GROUP']
    fig, ax = plt.subplots(figsize=(7.0, 2.65), layout='constrained')
    positions = np.arange(len(protocols))
    for offset, (model, data, color) in zip([-.18, .18], [('LR', lr, '#1875ae'), ('RF', rf, '#d56e27')]):
        values = [data[(data.protocol == p) & (data.variant == 'FULL')].iloc[0].f1 for p in protocols]
        bars = ax.bar(positions + offset, values, .34, label=model, color=color)
        ax.bar_label(bars, labels=[f'{v:.4f}' if 0 < v < .001 else f'{v:.3f}' for v in values], padding=2, fontsize=8)
    ax.set_xticks(positions, ['Row 70/30', 'Token fold 1', 'Token fold 2', 'Token fold 3', 'Exact-vector'])
    ax.set_ylim(0, 1.03)
    ax.set_ylabel('Tunnel F1')
    ax.legend(loc='lower right', bbox_to_anchor=(1, 1.01), ncol=2, frameon=False)
    ax.grid(axis='y', alpha=.18)
    ax.set_axisbelow(True)
    for extension in ['pdf', 'png']:
        buffer = io.BytesIO()
        fig.savefig(buffer, format=extension, dpi=200)
        (FIGURES / ('fixed_split_models.' + extension)).write_bytes(buffer.getvalue())
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.6), layout='constrained')
    for ax, (model, data) in zip(axes, [('LR', lr), ('RF', rf)]):
        mat = np.asarray([[data[(data.protocol == p) & (data.variant == v)].iloc[0].f1
                           for v in VARIANTS] for p in protocols[:4]])
        ax.imshow(mat, vmin=0, vmax=1, cmap='Blues', aspect='auto')
        for (i, j), value in np.ndenumerate(mat):
            ax.text(j, i, f'{value:.2f}', ha='center', va='center',
                    color='white' if value > .6 else '#16304a', fontsize=8)
        ax.set_xticks(np.arange(len(VARIANTS)), [LABELS[v] for v in VARIANTS],
                      rotation=45, ha='right', fontsize=7)
        ax.set_yticks(np.arange(4), ['Row', 'G1', 'G2', 'G3'])
        ax.set_title(model + ': F1 after feature removal', fontsize=9)
        ax.tick_params(length=0)
    for extension in ['pdf', 'png']:
        buffer = io.BytesIO()
        fig.savefig(buffer, format=extension, dpi=200)
        (FIGURES / ('proxy_ablations.' + extension)).write_bytes(buffer.getvalue())
    plt.close(fig)
    print('Built nine measured tables, two figures and generated numeric macros.')


if __name__ == '__main__':
    main()
