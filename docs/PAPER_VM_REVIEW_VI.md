# Biên bản đối chiếu gói chạy VM — 04/11/2026

Gói nhận: `IAM302t_Paper_VM_Evidence_20261104.tar.gz` (9.048.231 byte; 130 file). SHA-256: `de00abb0daa0d979c56d1cef788c8ab761dbebe969c76474334d6952a96189e1`.

Đã đọc archive, log và prediction arrays; các nhận định dưới đây không chỉ dựa trên ảnh Terminal. Receipt máy đọc được nằm tại `results/PAPER_VM_RECEIPT_VALIDATION.json`.

| Hạng mục | Đối chiếu đã thực hiện | Kết quả |
|---|---|---|
| Mã nhận được | So SHA-256 của 15 script với bản phát hành trước lần chạy | Trùng toàn bộ |
| Môi trường | Python 3.12.16; so đúng tên/phiên bản 18 package với requirements-lock | Khớp |
| Split | SHA-256 NPZ, dataset binding, indices và nhóm test | Giữ nguyên |
| 50 cấu hình CIC gốc | Tính confusion counts và metrics từ prediction arrays, đối chiếu nhãn CSV gốc | Khớp; đây là kiểm tra kết quả có sẵn, không phải huấn luyện lại cả 50 cấu hình trong lần này |
| 8 refits RF/LR | So indices, nhãn thật, nhãn dự đoán và chỉ số với bằng chứng cũ | Khớp nhãn từng dòng |
| 8 cohort summaries | Tính lại mean/median/fraction từ score từng dòng của cả benign và attack | Khớp CSV |
| 4 CTU controls | Tính lại confusion matrices, so LR8 với LR7 bỏ DOTS | Khớp; 0 dự đoán khác nhau ở cả hai biểu diễn |
| Nguồn CTU | So MD5/SHA-256 và metadata originals/binary với bản đã xác minh | Khớp |
| Mã CTU liên quan | So SHA-256 bốn file ở commit đã ghim | Khớp |
| Đường đi RF | Tái tính tổng baseline + contributions và trung bình score lá của 100 cây | Khớp score RF |

## Khác biệt số học được ghi nhận

Các nhãn dự đoán và confusion matrices vẫn trùng. RF refit scores cũng trùng chính xác ở precision đã lưu; cohort RF chỉ có sai khác số học khoảng 2,22e-16. Một số score LR khác giữa hai lần thực thi:

- Input quan sát: sai khác tuyệt đối lớn nhất khoảng **0,004524**.
- Input thay prototype: lớn nhất khoảng **0,005063**.
- Không có mẫu đổi phía ngưỡng 0,5 trong các mảng cohort đã đối chiếu.

Chưa thực hiện thí nghiệm cô lập nguyên nhân nên không gán khác biệt này cho riêng Python, CPU hay BLAS. Bản báo cáo cập nhật dùng score trên VM; các số liệu cũ nằm trong `legacy/revision_v2_reference/` để đối chiếu.

Ví dụ median LR của benign sau substitution đổi từ 0,1169 lên 0,1171 khi làm tròn bốn chữ số. Vì vậy cần sinh lại bảng/hình thay vì chỉ sửa tên phiên bản môi trường.

## Trạng thái nghiên cứu

Bước tái lập các kết quả gốc đã hoàn tất. Gói VM ban đầu không chứa thí nghiệm seed. Gói RF seed nhận sau đó đã bổ sung và kiểm chứng đủ 30 cấu hình; chi tiết ở `PAPER_RF_SEED_REVIEW_VI.md`. Chưa có registrable-domain holdout thật và chưa tái lập checkpoint MC-CNN gốc.

## Bổ sung gói RF seed cùng ngày

Đã kiểm tra gói `IAM302t_RF_Seeds_20261104.tar.gz`, SHA-256 `bd0abdfec8b190c54d99c22d8e4d6d0120a6e678fbd4c03b97b140173aeefe2f`. Đủ 30 NPZ, 6 summaries, 15 paired differences và 6 baseline matches. Chiều ablation giữ nguyên ở mọi seed trên từng fold; bảng/hình và kết luận đã cập nhật. Receipt riêng ở `results/paper_rf_seeds/verification.json`.
