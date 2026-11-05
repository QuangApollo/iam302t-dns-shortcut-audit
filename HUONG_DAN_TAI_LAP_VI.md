# Hướng dẫn tái lập — IAM302t, Nhóm 3

Các lệnh chạy trong thư mục `IAM302t_HuongB_Revised` sau khi giải nén. Môi trường VM đã dùng Python 3.12.16 và 18 gói khóa phiên bản trong `requirements-lock.txt`; `VM_ENVIRONMENT.json` ghi phiên bản thực tế. Split được tạo trước đó dưới Python 3.12.14 và giữ nguyên byte khi chạy trên VM.

## 1. Chuẩn bị môi trường trên Ubuntu/Kali

Máy mới cần Internet để tải Python và các gói. Nếu đã có `.venv312` với các thư viện tương ứng thì dùng trực tiếp môi trường đó.

```bash
cd ~/IAM302t_HuongB_Revised
wget -qO- https://astral.sh/uv/install.sh | sh
~/.local/bin/uv venv --python 3.12.16 .venv312
~/.local/bin/uv pip install --python .venv312/bin/python -r requirements-lock.txt
.venv312/bin/python --version
```

Các lệnh sau gọi trực tiếp Python của môi trường ảo nên dùng được khi mở Terminal mới. Không cần cài lại Python hệ thống.

## 2. Kiểm tra kết quả đã lưu

```bash
sha256sum -c MANIFEST_SHA256.txt
.venv312/bin/python source/run_steps.py verify
.venv312/bin/python source/prepare_ctu.py --verify-binary-only
```

Kiểm tra manifest ngay sau khi giải nén, trước khi chạy các lệnh cập nhật kết quả. Cần thấy PASS cho 25 cấu hình LR, 25 cấu hình RF, hash CIC/split, tính tách biệt SLD và checksum hai file CTU binary. `verify` tính lại chỉ số từ dự đoán từng dòng; nó không huấn luyện lại mô hình.

## 3. Chạy lại từng bước

```bash
.venv312/bin/python source/run_steps.py 1
.venv312/bin/python source/run_steps.py 2
.venv312/bin/python source/run_steps.py 3
.venv312/bin/python source/run_steps.py 4
.venv312/bin/python source/run_steps.py 5
.venv312/bin/python source/build_report_assets.py
.venv312/bin/python source/build_revision_assets.py
```

| Bước | Nội dung | Kết quả chính |
|---|---|---|
| 1 | Kiểm toán CIC và các phép chia đã lưu | `results/dataset_audit.json`, `split_inventory.csv`, `vector_overlap.csv` |
| 2 | LAB: 24 trường hợp missing values, ablation proxy; dự đoán PTR từ TTL | `lab/results/`, `results/qtype_proxy_results.csv` |
| 3 | LR/RF: 50 cấu hình chính; RF tham khảo 41 cột | `results/lr_results.csv`, `rf_results.csv`, `reference_inventory_results.csv`, `predictions/` |
| 4 | Xác minh CTU binary và kiểm toán biểu diễn | `results/ctu_structure.csv`, `ctu_results.csv` |
| 5 | Kiểm tra confusion matrix, chỉ số và checksum | `results/validation.json`, `logs/05_verify.log` |

Có thể thay năm lệnh bước bằng `.venv312/bin/python source/run_steps.py all`. Bước 3 tốn thời gian huấn luyện; các bước mặc định sử dụng dữ liệu đã kèm và không cần tải CTU raw. Giữ nguyên `splits/frozen_splits.npz` và `splits/metadata.json`; không gọi `freeze` để chọn lại phép chia.

Muốn tải lại CTU raw từ nguồn công bố, xác minh MD5 và tạo binary từ đầu:

```bash
.venv312/bin/python source/run_steps.py 4 --download
```

Script giữ class 0/2, chép nguyên trường domain và ghi nguồn/checksum trong `results/ctu_preparation.json`. Dữ liệu raw được tải khi yêu cầu, không nằm trong bộ nộp.

## 4. Chạy lại các chẩn đoán theo nhận xét cuối (bản 03/11)

Các kết quả mới đã lưu trong `results/revision_v2/`. Có thể kiểm tra mà không fit lại:

```bash
.venv312/bin/python source/verify_revision.py
```

Muốn chạy lại phần cơ chế (8 refits + 2 fits kiểm tra cohort):

```bash
.venv312/bin/python source/revision_v2_diagnostics.py
.venv312/bin/python source/revision_v2_cohort_probe.py
```

Muốn kiểm tra lại originals CTU và mã tiền xử lý được ghim commit:

```bash
.venv312/bin/python source/prepare_ctu.py --download
.venv312/bin/python source/revision_v2_ctu.py --originals data/ctu/raw
.venv312/bin/python source/trace_ctu_source.py --download
.venv312/bin/python source/verify_revision.py
```

Việc tải CTU raw và mã tác giả cần Internet. Các phép thay name inputs là probe nhân tạo, không phải điểm detector cải thiện. GROUP chỉ đo nhạy cảm theo token thô; không tái tạo split theo registrable domain.

Các diagnostic bổ sung đã được chạy lại trên VM Python 3.12.16 ngày 04/11/2026; đủ 18 package khớp lock. Gói thực chạy và receipt nằm trong `evidence/IAM302t_Paper_VM_Evidence_20261104.tar.gz` và `results/PAPER_VM_RECEIPT_VALIDATION.json`. Bản tham chiếu Python 3.12.14 nằm trong `legacy/revision_v2_reference/`. Dự đoán nhãn khớp, một số score LR chênh nhẹ; bảng/hình dùng kết quả VM. `verify_revision.py` giữ nguyên receipt và log VM gốc.

## 5. Biên dịch báo cáo

Sau khi sinh lại assets, sử dụng TeX Live có XeLaTeX:

```bash
cd report
latexmk -xelatex -interaction=nonstopmode -halt-on-error -jobname=IAM302t_HuongB_Revised_IEEE main.tex
latexmk -xelatex -interaction=nonstopmode -halt-on-error -jobname=IAM302t_HuongB_Supplement supplement.tex
```

IEEEtran và font Liberation đã kèm. Khi dùng Overleaf, tải ZIP Overleaf đi kèm thành một project mới, chọn compiler XeLaTeX và biên dịch `main.tex` và `supplement.tex` (đổi Main document khi cần). Hai báo cáo dùng chung các bảng/hình và file availability.

## 6. Đối chiếu các số liệu chính

- CIC: 228.042 dòng; 156.014 benign; 72.028 attack; 86.866 dòng trùng hoàn toàn sau lần đầu; 1.000 nhóm vector có cả hai nhãn.
- RF FULL: ROW F1 0,8864; GROUP 1/2/3 lần lượt 0,8862 / 0,0004 / 0,6883; mean F1 0,5250; pooled F1 0,6877.
- LAB: GRAPH F1 1,0000 trong thiết kế hiện có; HYBRID zero-fill có 6 FP, train-median có 4 FP. Đây là chẩn đoán trên lab đã quan sát.
- CTU: 950.547 dòng train và 237.631 dòng test; LENGTH full F1 0,6484; LR8 full 0,2515; LR8 first-label 0,1432.

Các phép kiểm tra này không biến baseline CIC thành bản tái lập hybrid hai tầng của nguồn gốc. Phạm vi thí nghiệm và các đầu vào còn thiếu được ghi trong báo cáo và `docs/DOI_CHIEU_PHUONG_PHAP_GOC_VI.md`.

## 7. Đọc bản sửa và hoàn tất link mã công khai

Bài chính có 5 trang, 2 bảng + 2 hình; phụ lục 6 trang giữ đầy đủ kết quả. `docs/PHAN_HOI_NHAN_XET_CUOI_VI.md` đối chiếu từng nhận xét mới. **Chưa có URL public repo xác minh được**; theo `docs/XUAT_BAN_GITHUB_VI.md` để publish bằng tài khoản của bạn và gắn URL thật, rồi compile lại. Không cần thay dữ liệu hoặc huấn luyện lại vì bước publication này.

Sau khi sửa bất kỳ file nào, checksum manifest cũ sẽ không còn đúng cho file đó. Chỉ so manifest ngay sau giải nén. Gói repository gọn không chứa dữ liệu công khai lớn và bằng chứng legacy; `source/download_public_data.py` khôi phục đúng dữ liệu cần thiết từ release có checksum.

## 8. Kiểm tra thí nghiệm RF qua 5 seed đã hoàn tất

Đủ 30 cấu hình, 6 baseline matches, 6 summaries và 15 paired differences đã được kiểm chứng. Sau khi giải nén bản nguồn mới và cài môi trường, chạy:

```bash
.venv312/bin/python source/verify_rf_seed_check.py
```

Trong bản nguồn đầy đủ, trước khi chạy lại các fit, có thể đối chiếu mọi member với archive VM gốc:

```bash
.venv312/bin/python source/verify_rf_seed_check.py --check-received-archive
```

`results/paper_rf_seeds/` giữ đủ dự đoán và execution log. Verifier ghi receipt riêng, không sửa NPZ hay log gốc. Gói repo gọn bỏ archive lớn nhưng vẫn giữ đủ evidence để kiểm tra metric sau khi khôi phục dữ liệu. Xem `docs/PAPER_RF_SEED_REVIEW_VI.md` để diễn giải kết quả và `docs/PAPER_NEXT_STEPS_VI.md` cho bước chuẩn bị gửi paper.
