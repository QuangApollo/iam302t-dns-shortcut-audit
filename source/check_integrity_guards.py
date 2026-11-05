#!/usr/bin/env python3
"""Exercise failure paths that protect the frozen experiment from accidental edits."""
import tempfile
from pathlib import Path
import numpy as np
import audit_pipeline as audit


def main():
    original_data = audit.DATA
    before = audit.sha256(audit.ROOT / 'splits/frozen_splits.npz')
    with tempfile.TemporaryDirectory() as d:
        changed = Path(d) / 'changed.csv'
        changed.write_text('different dataset bytes\n')
        audit.DATA = changed
        try:
            try:
                audit.read_data()
            except SystemExit as error:
                assert 'CSV bytes changed' in str(error)
            else:
                raise AssertionError('A modified dataset was accepted')
        finally:
            audit.DATA = original_data
    try:
        audit.freeze()
    except SystemExit as error:
        assert 'already exist' in str(error)
    else:
        raise AssertionError('Existing split indices were regenerated')
    try:
        audit.checked_split(np.array([0, 1]), np.array([1, 2]), 4)
    except AssertionError:
        pass
    else:
        raise AssertionError('Overlapping train/test indices were accepted')
    assert before == audit.sha256(audit.ROOT / 'splits/frozen_splits.npz')
    print('PASS: changed CSV rejected; existing splits protected; overlapping indices rejected')


if __name__ == '__main__':
    main()
