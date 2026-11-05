# DNS tunneling audit — IAM302t Group 3

**Paper:** *Auditing Shortcut Dependencies in DNS Tunneling: Residual Information across Models and Splits*. Revision 4, November 4, 2026; all 30 planned RF seed cases executed and independently verified.  
**Authors:** Mai Chí Thành; Đỗ Quang Thuận; Nguyễn Lê Quốc Bảo; Đặng Nguyễn Phương Thảo. IA2007, FPT University. Instructor: Mai Hoàng Đỉnh.  
[Vietnamese guide](README_VI.md) · [Reproduction](HUONG_DAN_TAI_LAP_VI.md) · [Response to feedback](docs/PHAN_HOI_NHAN_XET_CUOI_VI.md).

The central result is that deleting named columns does not necessarily delete the information they carry. TTL predicts record type, RF and LR respond differently to frozen coarse-token folds, and deleting a constant dot-count feature does not align CTU train/test string representations.

## Read the reports

- `report/IAM302t_HuongB_Revised_IEEE.pdf`: focused main paper, 5 pages, 2 tables and 2 figures.
- `report/IAM302t_HuongB_Supplement.pdf`: complete numeric audit, controls, seed results, and provenance, 6 pages.
- `docs/CTU_PIPELINE_TRACE.md`: verified source exposure versus unverified original neural-score impact.

## Reproduce or verify

Create a Python 3.12 environment and install `requirements-lock.txt`. The project VM uses Python 3.12.16 and all 18 installed packages match the lock file. Additional mechanism, cohort, and CTU controls were rerun there on November 4. Earlier Python 3.12.14 diagnostic outputs are preserved in `legacy/revision_v2_reference/`; labels agree, while some LR scores differ slightly.

```bash
python3 -m venv .venv312
.venv312/bin/python -m pip install -r requirements-lock.txt
# Compact public-repository package only: restore the checksum-pinned public data.
.venv312/bin/python source/download_public_data.py
# The complete submission ZIP already includes these data and can skip that download.
.venv312/bin/python source/verify_revision.py
.venv312/bin/python source/verify_rf_seed_check.py
```

Verification recomputes 50 original CIC cases, checks 8 prediction-identical refits, recomputes cohort score summaries from per-row arrays, and validates 4 CTU controls. It does not refit the models. See the Vietnamese reproduction guide for optional refits and report compilation. Never regenerate `splits/frozen_splits.npz` to choose a more favorable split.

## Evidence and provenance

- Primary CIC copy: Saravanan Rajan, *Feature-Based DNS Traffic Dataset for Heavy Attack Detection*, Zenodo v1, DOI [10.5281/zenodo.18139853](https://doi.org/10.5281/zenodo.18139853), deposited under CC BY 4.0. The audited CSV SHA-256 is `62ec5d632c9e665851c551487d6d1e2afbc7f8f55b62cac4649999dadafc89de`. Packet-to-row lineage to the original CIC release is not established by this byte match.
- CTU: Palau et al., *DNS Threats Dataset*, [Zenodo 6508640](https://zenodo.org/records/6508640); publisher MD5 and original/binary SHA-256 in `results/ctu_preparation.json`. The 2020 five-tool follow-up is a separate dataset.
- Associated preprocessing inspection: [harpomaxx/deepseq](https://github.com/harpomaxx/deepseq), pinned commit and per-file hashes in `results/revision_v2/ctu_source_trace.json`.
- `sld` is a grouping-only token in the primary 43-input RF/LR pipeline. GROUP folds measure coarse-token sensitivity, not validated registered-domain generalization.
- Artificial name-prototype substitution measures fixed-model score sensitivity; it is not a repaired detector or a traffic intervention.

The full submission archive preserves original VM logs and legacy evidence. The compact repository package includes current code, frozen splits, current measured outputs, and reproduction instructions; large public data are restored with the script above.

## AI disclosure

ChatGPT (OpenAI) assisted wording, code drafting, literature lookup, diagnostic design, and figures. Numerical results come from executed scripts and saved evidence. Authors remain responsible for review, interpretation, and submission.

## Publication status

`CODE_AVAILABILITY.json` records the current public-repository status. Until a repository is actually published and verified, the reports do not assert a public URL. Follow `docs/XUAT_BAN_GITHUB_VI.md` to finish publication and regenerate the reports.

## VM evidence received November 4

`evidence/IAM302t_Paper_VM_Evidence_20261104.tar.gz` preserves the received execution archive. `results/PAPER_VM_RECEIPT_VALIDATION.json` records source/split/package checks, independent recomputation, label equality, and score differences. `logs/paper_vm/07_environment.json` lists the actual VM installation. Current report figures/tables use the VM outputs.

See `docs/PAPER_NEXT_STEPS_VI.md` for the next research checkpoint. A robustness experiment across preset RF seeds is prepared in `source/paper_rf_seed_check.py`; its results are not yet reported as findings.

## RF seed experiment completed November 4

All 30 fixed cases (5 forest seeds × 3 coarse-token folds × FULL/no-name) were executed on the VM. Independent verification recomputes every confusion matrix, six summaries and 15 paired comparisons, and confirms the six seed-42 baselines. Ablation direction persists at every seed on each fold. GROUP-2 FULL F1 is 0.000381–0.004641 versus about 0.7759 without name statistics, whose FPR remains about 28.1%. Seed variation reuses the same test rows and does not represent independent deployment samples. See `docs/PAPER_RF_SEED_REVIEW_VI.md`. The received archive is retained in the complete source package; the compact repo keeps its execution log with the results.
