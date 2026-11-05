#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$ROOT/src/run_day1_s08.py" | tee "$ROOT/results/00_run_log.txt"
echo "DONE: $ROOT/results / $ROOT/figures"
