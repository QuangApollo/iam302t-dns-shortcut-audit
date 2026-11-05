# Biên dịch báo cáo đã đối chiếu VM 04/11/2026

Gói Overleaf có đầy đủ main/supplement, bảng/hình đo thực, IEEEtran và font Liberation.

1. Upload ZIP này thành project mới.
2. Chọn compiler **XeLaTeX**.
3. Main document `main.tex` tạo bài chính (5 trang).
4. Đổi Main document sang `supplement.tex` tạo phụ lục đầy đủ (6 trang).

`metrics.tex`, `tables/`, `figures/` được sinh từ các CSV trong gói mã nguồn đầy đủ. Overleaf không cần chạy Python. Cả hai báo cáo có thể compile độc lập trong thư mục này.

`code_availability.tex` ghi trạng thái thật của kho mã. Khi repository đã public và xác minh đúng dự án, cập nhật URL trong file đó rồi compile lại. Bản hiện tại chưa có URL public; không tự thay bằng địa chỉ minh họa.

`archive/main_submitted_2026_11_01.tex` chỉ là nguồn lưu bản trước trong gói đầy đủ, không phải main document; gói Overleaf nộp lại chỉ dùng hai nguồn hiện hành.
