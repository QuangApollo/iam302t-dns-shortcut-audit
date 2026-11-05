#!/usr/bin/env python3
"""Run the ordered repair/reproduction steps; never regenerate frozen indices."""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(name, command):
    print('\nSTEP:', name, flush=True)
    log = ROOT / 'logs' / (name + '.log')
    with log.open('w') as f:
        p = subprocess.Popen([sys.executable, *command], cwd=ROOT, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True)
        for line in p.stdout:
            print(line, end='', flush=True)
            f.write(line)
        code = p.wait()
    if code:
        raise SystemExit(f'{name} failed; inspect {log}')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('step', choices=['1', '2', '3', '4', '5', 'all', 'verify'])
    p.add_argument('--download', action='store_true', help='Allow CTU public downloads in step 4')
    args = p.parse_args()
    selected = ['1', '2', '3', '4', '5'] if args.step == 'all' else [args.step]
    for step in selected:
        if step == '1':
            run('01_cic_integrity_audit', ['source/audit_pipeline.py', 'audit'])
        elif step == '2':
            run('02_lab', ['lab/src/run_day1_s08.py'])
            run('02_qtype_proxies', ['source/audit_pipeline.py', 'proxies'])
        elif step == '3':
            run('03_lr', ['source/audit_pipeline.py', 'experiments', '--model', 'LR'])
            run('03_rf', ['source/audit_pipeline.py', 'experiments', '--model', 'RF'])
            run('03_reference_inventory', ['source/audit_pipeline.py', 'reference'])
        elif step == '4':
            run('04_ctu_prepare', ['source/prepare_ctu.py'] + (['--download'] if args.download else ['--verify-binary-only']))
            run('04_ctu_audit', ['source/ctu_audit.py'])
        elif step in ('5', 'verify'):
            run('05_verify', ['source/audit_pipeline.py', 'verify'])


if __name__ == '__main__':
    main()
