# Kết quả kiểm chứng RF qua 5 seed — 04/11/2026

**Hoàn tất 30/30 cấu hình trên VM và kiểm chứng độc lập từ từng dòng dự đoán.** Bài chính và phụ lục đã cập nhật kết quả này. Không chọn seed có điểm cao nhất để thay baseline.

## Gói nhận và kế hoạch

- File: `IAM302t_RF_Seeds_20261104.tar.gz`, 4.525.254 byte, 38 file thường.
- SHA-256: `bd0abdfec8b190c54d99c22d8e4d6d0120a6e678fbd4c03b97b140173aeefe2f`.
- Kế hoạch canonical SHA-256: `01a189ae5822b62271e98a2b85b413630388f11ede7bb7011fd607f7d7c1a33e`.
- 5 seed cố định: **42, 0, 1, 7, 2026**; cả GROUP 1/2/3; FULL và NO_DOMAIN.
- Giữ nguyên dữ liệu, indices, preprocessing, 100 cây, max_depth=16 và min_samples_leaf=2. Chỉ đổi random seed của forest.
- Kế hoạch lưu trước lần fit bổ sung; đây không phải đăng ký trước trên registry công khai.
- Log ghi nhận đủ 30 lần fit. Metadata dùng Python 3.12.16; các phiên bản thư viện ghi trong metadata khớp receipt VM trước.

## Kết quả đầy đủ theo fold

| Fold | Đặc trưng | F1 nhỏ nhất | F1 trung vị | F1 lớn nhất |
|---|---|---:|---:|---:|
| GROUP_1 | FULL | 0.886002 | 0.886325 | 0.886487 |
| GROUP_1 | Bỏ 14 name statistics | 0.000000 | 0.001576 | 0.044275 |
| GROUP_2 | FULL | 0.000381 | 0.000381 | 0.004641 |
| GROUP_2 | Bỏ 14 name statistics | 0.775907 | 0.775907 | 0.775950 |
| GROUP_3 | FULL | 0.677327 | 0.687893 | 0.688258 |
| GROUP_3 | Bỏ 14 name statistics | 0.333996 | 0.333996 | 0.334007 |

`NO_DOMAIN` là tên file lịch sử, có nghĩa bỏ 14 numeric name statistics. Nó không có nghĩa đã loại mọi thông tin domain; `sld` chỉ dùng để chia nhóm, không phải input RF chính.

## Diễn giải

1. **GROUP 2 FULL sụp ở cả 5 seed:** chỉ phát hiện 5–61 trong 26.207 attack rows. F1 dao động 0,000381–0,004641. Bỏ name statistics cho F1 khoảng 0,7759, nhưng FPR vẫn **28,11–28,13%**; đây chưa phải một detector cải thiện đủ để triển khai.
2. **GROUP 1 có chiều tác động ngược lại:** FULL ổn định gần 0,8863; bỏ name statistics làm F1 xuống 0–0,044275. Cần công bố seed 2026 có F1 0,044275, không viết mọi seed đều giống hệt seed 42.
3. **GROUP 3:** FULL khoảng 0,6773–0,6883, cao hơn no-name khoảng 0,3340 ở mọi seed.
4. 15 hiệu F1 theo cặp cùng seed/fold đều giữ cùng dấu: FULL cao hơn trên GROUP 1/3 và thấp hơn trên GROUP 2. Do đó ablation reversal lặp lại dưới forest randomness trong thiết kế đã cố định.

Min/median/max trên đây là biến thiên mô hình trên **cùng test rows**. Không diễn giải chúng thành confidence interval từ 5 capture độc lập hoặc thành bằng chứng tổng quát hóa theo domain/family/time. Các kiểm tra path/prototype vẫn thuộc mô hình seed 42; chưa có phân tích cơ chế riêng cho mọi seed.

## Những gì đã kiểm tra

| Hạng mục | Kết quả |
|---|---|
| Kế hoạch nhận được so với plan đã chốt | Khớp toàn bộ grid 30 cấu hình |
| Script chạy và hai module pipeline | SHA-256 khớp plan; script nhận được trùng bản đã phát hành |
| Dataset/split | Đúng bytes; test indices giữ nguyên và coarse token tách biệt |
| 30 NPZ | Đúng shape, indices, nhãn CSV, nhãn dự đoán và probability hợp lệ |
| Chỉ số từng trường hợp | Tính lại TN/FP/FN/TP, accuracy, precision, recall, F1, FPR và median attack score |
| Seed 42 | Cả 6 bộ predicted labels khớp baseline gốc |
| Tổng hợp | Tái tính 6 min/median/max summaries và 15 hiệu theo cặp |
| Gói gốc | Mọi member nhận được khớp byte với file giữ lại trong bản nguồn đầy đủ |

Receipt: `results/paper_rf_seeds/verification.json`. Verifier mới `source/verify_rf_seed_check.py` dùng nhãn CSV và phép đếm trực tiếp, không gọi hàm metric hay fit của script thí nghiệm.

## Đọc và tái kiểm tra

Trong gói nguồn mới, sau khi cài môi trường theo hướng dẫn:

```bash
.venv312/bin/python source/verify_rf_seed_check.py
```

Bản nguồn đầy đủ có thể đối chiếu thêm từng byte của archive gốc, trước khi chạy lại fit ghi đè kết quả:

```bash
.venv312/bin/python source/verify_rf_seed_check.py --check-received-archive
```

Gói repository gọn giữ execution log trong `results/paper_rf_seeds/execution.log`, bỏ các archive lớn. Kiểm tra prediction/metric vẫn chạy sau khi khôi phục dữ liệu bằng `source/download_public_data.py`; kiểm tra archive chỉ áp dụng cho bản nguồn đầy đủ. File `run_metadata.json` có trường `environment.seed=42` của baseline chung; seed của từng fit được lưu riêng trong plan, tên file và từng NPZ.

## Việc tiếp theo để chuẩn bị bản gửi paper

Bước thí nghiệm seed đã xong. Cần tiếp tục đối chiếu toàn văn công trình gần nhất, chốt nơi nộp và yêu cầu ẩn danh/page limit, chuẩn bị artifact phù hợp, rồi để toàn bộ tác giả đọc và duyệt nội dung. Chưa có URL repository công khai được xác minh và chưa chọn venue cụ thể.
