# IAM302t — Nhóm 3, lớp IA2007

**Đề tài:** Auditing Shortcut Dependencies in DNS Tunneling: Residual Information across Models and Splits.  
**Thành viên:** Mai Chí Thành; Đỗ Quang Thuận; Nguyễn Lê Quốc Bảo; Đặng Nguyễn Phương Thảo.  
**Giảng viên:** Mai Hoàng Đỉnh — FPT University.  
**Bản sửa:** 05/11/2026, đã đối chiếu kết quả VM và xác minh kho mã GitHub công khai.

Bài chính `report/IAM302t_HuongB_Revised_IEEE.pdf` còn **5 trang, 2 bảng và 2 hình**. Phụ lục `report/IAM302t_HuongB_Supplement.pdf` giữ các kết quả đầy đủ (6 trang). Không thay dữ liệu CIC hoặc indices đã đóng băng.

## Những phần đã chỉnh

- Chốt luận điểm bỏ cột chưa chắc bỏ thông tin; CIC làm trường hợp chính.
- Giải thích RF GROUP 2 bằng đầu vào thật, ngưỡng cây, feature shift và probe score; 8 refits khớp dự đoán VM. `sld` chỉ dùng chia nhóm, không nằm trong 43 inputs chính.
- Gọi GROUP đúng mức là coarse-token sensitivity; không ghi là domain/family-disjoint.
- Nâng CTU mismatch thành kết quả chính; thêm kiểm tra bỏ DOTS và truy vết mã/bài gốc.
- Gom khung audit theo observation unit, giảm bảng, bổ sung related work, khai báo AI.

## File cần đọc

- `docs/PHAN_HOI_NHAN_XET_CUOI_VI.md`: đối chiếu từng nhận xét và phần còn thiếu.
- `HUONG_DAN_TAI_LAP_VI.md`: kiểm tra nhanh, chạy lại, biên dịch.
- `docs/CTU_PIPELINE_TRACE.md`: nguồn gốc và phạm vi kết luận về CTU.
- `docs/XUAT_BAN_GITHUB_VI.md`: URL kho mã đã xác minh và trạng thái các artifact.
- `results/revision_v2/verification.json`: kết quả kiểm tra mới; không thay receipt VM cũ.

## Kiểm tra nhanh

Sau khi tạo môi trường theo hướng dẫn, chạy trong thư mục dự án:

```bash
sha256sum -c MANIFEST_SHA256.txt
.venv312/bin/python source/verify_revision.py
.venv312/bin/python source/verify_rf_seed_check.py
```

Bộ nguồn đầy đủ đã chứa dữ liệu cần thiết. Gói repository gọn bỏ dữ liệu công khai lớn; dùng `.venv312/bin/python source/download_public_data.py` trước khi verify.

## Trạng thái trước khi nộp lại

Kho mã công khai: [https://github.com/QuangApollo/iam302t-dns-shortcut-audit](https://github.com/QuangApollo/iam302t-dns-shortcut-audit). Đã xác minh đủ **255/255 file, gồm 95 file NPZ**, trên nhánh `main`. Gói GitHub chứa đủ dự đoán đã lưu; tải dữ liệu công khai đúng checksum bằng `source/download_public_data.py` trước khi verify. Bộ nguồn đầy đủ kèm LMS đã có dữ liệu và log VM gốc. Hai PDF ghi URL thật. Các tác giả đọc lại bài và khai báo AI trước khi gửi thầy qua LMS.

## Cập nhật sau lần chạy VM 04/11

Đã nhận gói 130 file, kiểm tra 15 script trùng bản tham chiếu, split giữ nguyên và đủ 18 package đúng lock. Tính lại 50 cấu hình gốc, 8 refits, 8 cohort summaries và 4 CTU controls. Dự đoán nhãn khớp; một số score LR chênh tối đa khoảng 0,0051 giữa hai lần thực thi, chưa xác định riêng nguyên nhân. Bảng/hình hiện dùng score của VM. Receipt ở `results/PAPER_VM_RECEIPT_VALIDATION.json`.

Bước nghiên cứu tiếp theo và giới hạn kết luận ở `docs/PAPER_NEXT_STEPS_VI.md`. Đã hoàn tất và kiểm chứng 30 cấu hình RF qua 5 seed; kết quả đã đưa vào paper và phụ lục. Xem `docs/PAPER_RF_SEED_REVIEW_VI.md` và `results/paper_rf_seeds/verification.json`.
