# Đối chiếu với phương pháp CIC và phần thí nghiệm cần làm tiếp

Nguồn chính thức: https://www.unb.ca/cic/datasets/dns-exf-2021.html

Bài báo: DOI 10.1145/3507509.3507520. File đang sử dụng khớp bản phân phối Zenodo DOI 10.5281/zenodo.18139853. Đây là hai mức nguồn gốc khác nhau và đều được trích trong báo cáo.

## Phần đối chiếu đã làm

| Thành phần | Mô tả nguồn CIC | Bản sửa hiện tại |
|---|---|---|
| Dữ liệu | Có cả stateful và stateless, heavy/light, PCAP và nhãn theo thời gian | Có heavy-stateful CSV của bản phân phối thứ ba; chưa có chuỗi stateless ghép theo thời gian |
| Đặc trưng | 14 nhóm stateless và 16 nhóm stateful, có categorical và TTL list | RF tham khảo bổ sung dùng đủ 41 cột ngoài nhãn, TTL list lấy trung bình, categorical fit trên train |
| Chia dữ liệu | Xáo trộn, 70/30 | ROW stratified 70/30 seed 42, lưu chỉ số; khác biệt stratification được ghi rõ |
| Kiến trúc | Hai tầng; stateless trước, stateful phân tích lại khi tỷ lệ suspicious vượt ngưỡng | RF một tầng; chưa có gating |
| Cửa sổ | 100 packets, bước trượt 100; tỷ lệ suspicious δ=0,4 | CSV không có timestamp hoặc liên kết packet-window để xây đúng cửa sổ gốc |
| Bins xác suất | Benign [0;0,4), suspicious [0,4;0,7), malicious [0,7;1] | Baseline một tầng dùng predict mặc định của RF/LR |
| Hyperparameters và encoding | Tài liệu công khai không đủ để xác định mọi lựa chọn thực thi | Ghi rõ 100 cây, encoding train-only và toàn bộ tham số của các baseline |
| Điểm gốc | RF heavy accuracy/precision/F1: 99,97% | RF 41 cột: accuracy 91,90%, F1 0,8857; thuộc pipeline hiện tại |

Khoảng chênh giữa hai hệ thống không phải phép đo trực tiếp mức thổi phồng do shortcut. Các ablation trước/sau trong cùng pipeline của nhóm là đối chiếu có kiểm soát ở mức cột đầu vào.

## Trình tự làm tiếp để trả lời phần điểm công bố

1. Lấy bản phát hành gốc gồm benign/attack PCAP, heavy-stateless/heavy-stateful, mô tả thời gian gán nhãn và mã trích xuất nếu có. Tại thời điểm kiểm tra 01/11/2026, trang download chính thức hiển thị form thông tin và thông báo server error; bộ hiện tại chưa có thêm các file này.
2. Đối chiếu schema, số dòng, hash và cách tạo nhãn của từng nguồn. Xác định nhãn là từng query chứa payload hay toàn bộ khoảng thời gian capture. Kiểm tra một số truy vấn PTR và các trường TTL với gói tin gốc.
3. Ghép đúng thứ tự packet/window, tái tạo stateless-first và gating theo mô tả. Khóa train/test trước khi so sánh các biến thể và không dùng test để điều chỉnh ngưỡng.
4. Báo cáo baseline full theo cùng đơn vị đo, sau đó retrain khi bỏ IP, QTYPE, domain và các proxy đã đo. Mọi biến thể dùng cùng test windows; nêu rõ khác biệt không tái lập được từ tài liệu.
5. Thêm holdout theo ngày/capture/tool để phân biệt nhận diện kịch bản với hành vi tunnel. So sánh cả F1, FPR, support từng lớp và lỗi mẫu.

## Trình tự public source-IP audit

1. Dùng PCAP có cả benign và attack, kèm metadata thời gian/kịch bản.
2. Trích riêng IP nguồn của client, IP resolver/forwarder và IP trả lời DNS; không trộn ba ý nghĩa này.
3. Đếm nhãn theo source IP và theo capture. Chạy luật IP-only trên cùng phép chia; báo cáo cả trường hợp IP không tách được nhãn.
4. Kiểm tra ở nguồn có cùng client sinh cả hai loại traffic hoặc chia theo capture độc lập. Korving một lớp hiện tại chỉ là kiểm toán metadata, chưa cung cấp đối chứng này.

## Kho mã

Bộ source hiện tại có README, file khóa môi trường, script chạy từng bước và kết quả kiểm toán. Khi tạo kho mã thật, đưa URL có thể truy cập vào báo cáo. Không ghi URL dự kiến như thể kho đã tồn tại. Dữ liệu nặng có thể tải bằng script; giữ các checksum và frozen splits để tái lập đúng bản.
