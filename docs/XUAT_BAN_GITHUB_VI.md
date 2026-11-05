# Kho mã công khai và trạng thái bằng chứng

Kho mã của nhóm: [https://github.com/QuangApollo/iam302t-dns-shortcut-audit](https://github.com/QuangApollo/iam302t-dns-shortcut-audit). Chủ sở hữu: QuangApollo. Đã xác minh repository public, nhánh main và 187 file khớp Git blob hash ngày 05/11/2026. Commit kiểm tra: `e284e519e703e623f50c94671ae689cf7d94fb76`.

## Phần đã công khai

Mã nguồn, tài liệu, frozen splits, báo cáo, bảng/hình và các artifact tải lên thành công. Hai PDF bản mới đã ghi URL thật. Việc nộp môn học thực hiện qua LMS theo yêu cầu giảng viên.

## Phần chưa công khai

Bước duyệt tự động đã chặn một số thao tác đăng NPZ; lần đăng còn 68 đường dẫn NPZ chưa hoàn tất. Danh sách cụ thể nằm trong `CODE_AVAILABILITY.json`. Đây là các arrays phục vụ kiểm chứng; không sửa số liệu để tránh bước duyệt. Bộ nguồn đầy đủ và gói GitHub Ready tải về vẫn chứa đủ file.

## Tái lập khi dùng GitHub

Khôi phục dữ liệu đúng checksum bằng `source/download_public_data.py`. Giữ nguyên frozen splits. Khi còn thiếu saved arrays, chạy các fit ở mục 3 và 4 của `HUONG_DAN_TAI_LAP_VI.md`, rồi chạy `source/paper_rf_seed_check.py --resume` và các verifier. Việc này tạo lại kết quả tại máy người chạy; không tự công khai các file còn chờ.

Để kiểm tra saved outputs mà không fit lại, dùng gói nguồn đầy đủ đi kèm bộ nộp LMS. Các kết quả VM gốc và 30 seed cases đã được đối chiếu; lần cập nhật URL giữ nguyên dữ liệu và kết quả khoa học.

## Cập nhật PDF về sau

Hai báo cáo dùng chung `report/code_availability.tex`. Chọn XeLaTeX và biên dịch `main.tex`, `supplement.tex` nếu sửa nội dung hoặc URL. `source/set_repository_url.py` dùng cho môi trường có quyền truy cập API GitHub; lần này kiểm tra trực tiếp qua API được kết nối và lưu phạm vi trong `CODE_AVAILABILITY.json`.
