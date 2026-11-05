# Hoàn tất kho mã công khai và gắn URL thật vào báo cáo

Đây là yêu cầu còn thiếu trong nhận xét cuối. Mã và cấu trúc repository đã chuẩn bị; chưa có phiên đăng nhập GitHub để tạo kho và đẩy mã. Không cần cấp mật khẩu hoặc token trong tin nhắn.

## Cách 1 — Làm trong phiên ChatGPT đã kết nối GitHub

Kết nối tài khoản GitHub, hoặc cung cấp repository công khai đã tạo mà bạn có quyền ghi. Khi có kết nối/quyền ghi, có thể đăng gói đã chuẩn bị, xác minh URL công khai, cập nhật `code_availability.tex` và biên dịch lại. Các file hiện tại đã làm xong phần nội dung và số liệu, không cần làm lại thí nghiệm.

## Cách 2 — Đăng trên máy của bạn

Cài Git, GitHub CLI theo hướng dẫn chính thức của GitHub, rồi giải nén gói `IAM302t_Nhom3_GitHub_Ready.zip`. Chạy trong thư mục gói đó:

```bash
gh auth login
bash PUBLISH_GITHUB.sh
```

Script tạo repository công khai `iam302t-dns-shortcut-audit` trong tài khoản đã xác thực, commit và push mã. Có thể truyền tên khác làm đối số đầu tiên nếu tên đó đã được dùng. Script dừng nếu thư mục đã có git checkout; không ghi đè remote có sẵn.

## Gắn URL và tạo lại hai PDF

Sau khi repository đã có mã, chạy trong **bộ nguồn đầy đủ**. Thay URL dưới đây bằng URL thật được GitHub trả về; đây chỉ là minh họa cú pháp, không phải link công bố của nhóm:

```bash
.venv312/bin/python source/set_repository_url.py https://github.com/TEN_TAI_KHOAN/TEN_KHO_MA
cd report
latexmk -xelatex -interaction=nonstopmode -halt-on-error -jobname=IAM302t_HuongB_Revised_IEEE main.tex
latexmk -xelatex -interaction=nonstopmode -halt-on-error -jobname=IAM302t_HuongB_Supplement supplement.tex
```

Script kiểm tra repository thực sự public, chứa pipeline dự án và đúng dataset hash trong split metadata trước khi viết URL. Sau đó thay PDF trong bộ nộp và cập nhật manifest. Không chỉ sửa văn bản thành “public” khi repository chưa tồn tại.

Nếu dùng Overleaf: cập nhật `code_availability.tex` bằng URL đã kiểm tra, chọn XeLaTeX, biên dịch `main.tex` và `supplement.tex`. Hai báo cáo dùng chung file availability.
