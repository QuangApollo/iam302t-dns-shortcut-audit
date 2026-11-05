#!/usr/bin/env python3
"""Build focused revision figures and tables from the saved measured outputs."""
import io
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'report'
OUT = ROOT / 'results/revision_v2'


def save_figure(fig, name):
    for extension, options in [('pdf', {}), ('png', {'dpi': 220})]:
        buffer = io.BytesIO()
        fig.savefig(buffer, format=extension, **options)
        (REPORT / 'figures' / f'{name}.{extension}').write_bytes(buffer.getvalue())
    plt.close(fig)


def table(name, columns, header, rows):
    lines = [r'\centering\footnotesize', r'\begin{tabular}{@{}' + columns + r'@{}}',
             r'\toprule', ' & '.join(header) + r'\\\midrule']
    lines += [' & '.join(map(str, row)) + r'\\' for row in rows]
    lines += [r'\bottomrule', r'\end{tabular}']
    (REPORT / 'tables' / (name + '.tex')).write_text('\n'.join(lines) + '\n')


def main():
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 8,
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'pdf.fonttype': 42})
    (REPORT / 'figures').mkdir(exist_ok=True)
    rf = pd.read_csv(ROOT / 'results/rf_results.csv')
    lr = pd.read_csv(ROOT / 'results/lr_results.csv')
    proxy = pd.read_csv(ROOT / 'results/qtype_proxy_results.csv')
    overlap = pd.read_csv(ROOT / 'results/vector_overlap.csv')
    audit = json.loads((ROOT / 'results/dataset_audit.json').read_text())
    mechanism = json.loads((OUT / 'mechanism.json').read_text())
    cohort = pd.read_csv(OUT / 'cohort_input_sensitivity.csv')
    seed_dir = ROOT / 'results/paper_rf_seeds'
    seed_check = json.loads((seed_dir / 'verification.json').read_text())
    assert seed_check['all_checks_passed'] and seed_check['cases_recomputed'] == 30
    seed_cases = pd.read_csv(seed_dir / 'cases.csv')
    seed_summary = pd.read_csv(seed_dir / 'summary.csv')
    def score(data, protocol, variant, metric='f1'):
        return float(data[(data.protocol == protocol) & (data.variant == variant)].iloc[0][metric])
    p = proxy[(proxy.protocol == 'ROW') & (proxy.features == 'TTL_ONLY')].iloc[0]
    repeated = overlap[overlap.protocol == 'ROW'].iloc[0]
    table('cic_controls', 'p{4.35cm}r', ['Control / measurement', 'Observed result'], [
        ['Complete-row repeats beyond first', f"{audit['duplicate_full_rows_beyond_first']:,} (38.09\\%)"],
        ['Nonlabel vectors carrying both labels', f"{audit['conflicting_nonlabel_vector_groups']:,}"],
        ['ROW test rows matching a train vector', f"{int(repeated.test_rows_matching_train_nonlabel_vector):,} (39.18\\%)"],
        ['RF FULL F1: ROW $\\to$ exact-vector split',
         f"{score(rf, 'ROW', 'FULL'):.4f} $\\to$ {score(rf, 'EXACT_VECTOR_GROUP', 'FULL'):.4f}"],
        ['PTR from TTL only: ROW accuracy', f'{100*p.accuracy:.2f}\\%'],
        ['RF F1, no type/name $\\to$ also no TTL',
         f"{score(rf, 'ROW', 'NO_BOTH'):.4f} $\\to$ {score(rf, 'ROW', 'NO_BOTH_TTL'):.4f}"],
        ['LR F1, no type/name $\\to$ also no TTL',
         f"{score(lr, 'ROW', 'NO_BOTH'):.4f} $\\to$ {score(lr, 'ROW', 'NO_BOTH_TTL'):.4f}"],
    ])
    fig, axes = plt.subplots(1, 2, figsize=(7.05, 3.15),
                             gridspec_kw={'width_ratios': [1.35, 1]})
    fig.subplots_adjust(left=.065, right=.99, bottom=.16, top=.71, wspace=.38)
    positions = np.arange(2)
    specifications = [('RF', rf, 'FULL', '#bd5e26', ''),
                      ('RF', rf, 'NO_DOMAIN', '#efbb91', '//'),
                      ('LR', lr, 'FULL', '#176b9a', ''),
                      ('LR', lr, 'NO_DOMAIN', '#9bc5dc', '//')]
    for offset, (model, data, variant, color, hatch) in zip([-.27, -.09, .09, .27], specifications):
        values = [score(data, f'GROUP_{g}', variant) for g in [1, 2]]
        label = model + (' full' if variant == 'FULL' else ' without name stats')
        bars = axes[0].bar(positions + offset, values, .17, color=color, hatch=hatch,
                           edgecolor='white', linewidth=.35, label=label)
        label_tops = values
        if model == 'RF':
            ranges = [seed_summary[(seed_summary.protocol == f'GROUP_{g}') &
                                   (seed_summary.variant == variant)].iloc[0] for g in [1, 2]]
            axes[0].errorbar(positions + offset, values,
                             yerr=np.array([[v-r.f1_min for v, r in zip(values, ranges)],
                                            [r.f1_max-v for v, r in zip(values, ranges)]]),
                             fmt='none', ecolor='#303941', elinewidth=.8, capsize=2, zorder=4)
            label_tops = [r.f1_max for r in ranges]
        for x, value, top in zip(positions + offset, values, label_tops):
            axes[0].annotate(f'{value:.4f}', (x, top), xytext=(0, 3),
                             textcoords='offset points', ha='center', va='bottom',
                             fontsize=6.6, rotation=90)
    axes[0].set_xticks(positions, ['G1: token 192 held out', 'G2: token 224 held out'])
    axes[0].set_ylim(0, 1.17)
    axes[0].set_ylabel('Tunnel F1 on observed test rows')
    axes[0].set_title('(a) Model and feature dependence', fontsize=9, loc='left')
    axes[0].legend(loc='lower center', bbox_to_anchor=(.5, 1.15), ncol=2,
                   frameon=False, fontsize=7, columnspacing=.9, handlelength=1.3)
    axes[0].grid(axis='y', alpha=.17)
    axes[0].set_axisbelow(True)
    right = axes[1]
    for x, model in enumerate(['RF', 'LR']):
        values = [float(cohort[(cohort.model == model) & (cohort.actual_class == 1) &
                              (cohort.treatment == t)].iloc[0].median_probability)
                  for t in ['observed', 'name_family_train_attack_medians']]
        right.plot([x-.13, x+.13], values, color='#6e7881', linewidth=1.3, zorder=2)
        for j, (value, color, marker) in enumerate(zip(values, ['#213e53', '#ad4e21'], ['o', 'D'])):
            xpos = x + (-.13 if j == 0 else .13)
            right.scatter(xpos, value, color=color, marker=marker, s=36, zorder=3,
                          label=['Observed inputs', 'Training-attack name prototype'][j] if x == 0 else None)
            right.annotate(f'{value:.3f}', (xpos, value), xytext=(0, 8 if j else -13),
                           textcoords='offset points', ha='center', fontsize=8)
    right.axhline(.5, color='#6f7479', linewidth=.8, linestyle='--')
    right.text(1.43, .515, 'decision threshold', ha='right', fontsize=6.7, color='#555555')
    right.set_xticks([0, 1], ['RF full', 'LR full'])
    right.set_xlim(-.48, 1.48)
    right.set_ylim(0, 1.17)
    right.set_ylabel('Median attack score, G2 attack rows')
    right.set_title('(b) Artificial input-sensitivity probe', fontsize=9, loc='left')
    right.legend(loc='lower center', bbox_to_anchor=(.5, 1.15), frameon=False,
                 fontsize=6.8, handlelength=1.3)
    right.grid(axis='y', alpha=.17)
    save_figure(fig, 'rf_collapse_mechanism')

    structure = pd.read_csv(ROOT / 'results/ctu_structure.csv')
    fig, ax = plt.subplots(figsize=(3.45, 2.42), layout='constrained')
    colors = ['#174e70', '#76b2be', '#df8e4a']
    names = ['No dots', 'One dot', 'At least two']
    left = np.zeros(4)
    for column, color, label in zip(['zero_dots', 'one_dot', 'two_plus_dots'], colors, names):
        width = structure[column].to_numpy() / structure.rows.to_numpy() * 100
        ax.barh(np.arange(4), width, left=left, height=.58, color=color, label=label)
        for row, (begin, w) in enumerate(zip(left, width)):
            if w > 7:
                ax.text(begin+w/2, row, f'{w:.1f}%', ha='center', va='center', fontsize=7.5,
                        color='white' if column == 'zero_dots' else '#132c3e')
        left += width
    ax.set_yticks(np.arange(4), [f"{r['split'].title()} {'benign' if r.label == 0 else 'tunnel'}\nn={r.rows:,}"
                                 for _, r in structure.iterrows()])
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 25, 50, 75, 100], ['0', '25', '50', '75', '100%'])
    ax.set_xlabel('Share of canonicalized strings')
    ax.legend(loc='lower center', bbox_to_anchor=(.5, 1.01), ncol=3, frameon=False,
              fontsize=6.7, handlelength=1, columnspacing=.8)
    ax.spines[['left', 'bottom']].set_visible(False)
    ax.tick_params(axis='y', length=0)
    save_figure(fig, 'ctu_representation_shift')

    sensitivity = pd.read_csv(OUT / 'ctu_no_dots_control.csv')
    table('ctu_no_dots', 'llrrrr', ['Inputs', 'Test string', 'FP', 'TP', 'F1', 'FPR\\%'], [
        [r.model.replace('_', r'\_'), 'Full' if r.representation == 'FULL_STRING' else 'First label',
         f'{int(r.FP):,}', f'{int(r.TP):,}', f'{r.f1:.4f}', f'{100*r.fpr:.2f}']
        for _, r in sensitivity.iterrows()])
    table('input_sensitivity', 'llrr', ['Model', 'Actual class', 'Observed $p$', 'Prototype $p$'], [
        [model, 'Benign' if label == 0 else 'Attack'] + [
            f'{cohort[(cohort.model == model) & (cohort.actual_class == label) & (cohort.treatment == t)].iloc[0].median_probability:.4f}'
            for t in ['observed', 'name_family_train_attack_medians']]
        for model in ['RF', 'LR'] for label in [0, 1]])
    parts = pd.read_csv(OUT / 'rf_group2_path_contributions.csv')
    parts = parts.reindex(parts.contribution.abs().sort_values(ascending=False).index).head(8)
    table('path_components', 'lr', ['RF input', 'Mean path-score contribution'],
          [[r.feature.replace('_', r'\_'), f'{r.contribution:+.4f}'] for _, r in parts.iterrows()])
    original = pd.read_csv(OUT / 'ctu_original_representation.csv')
    table('ctu_original', 'llrrr', ['Split', 'Class', 'Rows', 'Any dot', 'Dot in first 45'], [
        [r['split'].title(), {0:'Benign',1:'DGA',2:'Tunnel'}[r.label], f'{r.rows:,}',
         f'{r.with_dot:,}', f'{r.prefix45_with_dot:,}'] for _, r in original.iterrows()])
    table('rf_seed_summary', 'llrrr', ['Fold', 'Inputs', 'Min F1', 'Median F1', 'Max F1'], [
        [r.protocol.replace('GROUP_', 'G'), 'Full' if r.variant == 'FULL' else 'No name',
         f'{r.f1_min:.6f}', f'{r.f1_median:.6f}', f'{r.f1_max:.6f}']
        for _, r in seed_summary.iterrows()])
    rows = []
    for protocol in ['GROUP_1', 'GROUP_2', 'GROUP_3']:
        for seed in [42, 0, 1, 7, 2026]:
            pair = seed_cases[(seed_cases.protocol == protocol) & (seed_cases.seed == seed)]
            full = pair[pair.variant == 'FULL'].iloc[0]
            removed = pair[pair.variant == 'NO_DOMAIN'].iloc[0]
            rows.append([protocol.replace('GROUP_', 'G'), seed, f'{full.f1:.6f}',
                         f'{removed.f1:.6f}', f'{full.FP:,}', f'{removed.FP:,}',
                         f'{full.TP:,}', f'{removed.TP:,}'])
    table('rf_seed_all_cases', 'lrrrrrrr',
          ['Fold', 'Seed', 'Full F1', 'No-name F1', 'Full FP', 'No-name FP', 'Full TP', 'No-name TP'], rows)
    macros = {}
    for group, word in [(1, 'One'), (2, 'Two'), (3, 'Three')]:
        for variant, label in [('FULL', 'Full'), ('NO_DOMAIN', 'NoName')]:
            row = seed_summary[(seed_summary.protocol == f'GROUP_{group}') &
                               (seed_summary.variant == variant)].iloc[0]
            for metric, suffix in [('f1_min', 'Min'), ('f1_median', 'Median'), ('f1_max', 'Max')]:
                macros[f'Seed{word}{label}{suffix}'] = f'{row[metric]:.4f}'
    (REPORT / 'rf_seed_metrics.tex').write_text(''.join(
        '\\newcommand{\\' + name + '}{' + value + '}\n' for name, value in macros.items()))
    fig, axes = plt.subplots(1, 3, figsize=(7.05, 2.52), sharey=True)
    fig.subplots_adjust(left=.065, right=.99, bottom=.19, top=.80, wspace=.12)
    offsets = np.linspace(-.12, .12, 5)
    for group, axis in enumerate(axes, 1):
        for x, variant, color in [(0, 'FULL', '#bd5e26'), (1, 'NO_DOMAIN', '#176b9a')]:
            subset = seed_cases[(seed_cases.protocol == f'GROUP_{group}') &
                                (seed_cases.variant == variant)].set_index('seed').loc[[42, 0, 1, 7, 2026]]
            axis.vlines(x, subset.f1.min(), subset.f1.max(), color=color, linewidth=1)
            for offset, (seed, row) in zip(offsets, subset.iterrows()):
                axis.scatter(x + offset, row.f1, color=color, s=25,
                             marker='D' if seed == 42 else 'o', zorder=3)
            axis.plot([x-.17, x+.17], [subset.f1.median()]*2, color=color, linewidth=1.4)
        axis.set_title(f'GROUP {group}', fontsize=9)
        axis.set_xticks([0, 1], ['Full', 'No name stats'])
        axis.set_xlim(-.42, 1.42)
        axis.set_ylim(-.025, 1.02)
        axis.grid(axis='y', alpha=.17)
        axis.set_axisbelow(True)
    axes[0].set_ylabel('Tunnel F1 on fixed test rows')
    fig.suptitle('Five fixed RF seeds per condition; diamonds mark seed 42', fontsize=9, y=.98)
    save_figure(fig, 'rf_seed_stability')
    assert mechanism['all_refit_predictions_match_saved_vm']
    print('Built focused CIC controls, RF mechanism, CTU shift, and verified five-seed tables/figures.')


if __name__ == '__main__':
    main()
