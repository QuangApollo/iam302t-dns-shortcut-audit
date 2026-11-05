# Kiểm toán dữ liệu lab S07/S08

Mã đang dùng: `src/run_day1_s08.py`. Từ thư mục gốc project, chạy:

```bash
.venv312/bin/python source/run_steps.py 2
```

Script đọc năm CSV trong `lab/data/`, xác minh baseline bốn cấu hình, chạy 24 trường hợp xử lý missing values và các ablation đặc trưng. Bảng nằm trong `lab/results/`, hai hình ở `lab/figures/`; log VM ở `logs/02_lab.log` của project.

`03_feature_ablation.csv` chứa cả ba phép bỏ riêng từng proxy graph. `06_dns_response_by_class.csv` ghi 114 SERVFAIL và 96 response trễ hơn 10 giây thuộc normal; một query tunnel chưa ghép response. Đây là dữ liệu đặc trưng đã trích xuất của nhóm; các thí nghiệm trong thư mục này không cần đọc lại PCAP.

S08 đã được quan sát trong quá trình chẩn đoán, nên các phép sensitivity/ablation là phân tích hậu nghiệm. 13 nhóm tunnel được cắt từ một phiên; chúng không tương đương 13 kịch bản độc lập. Với các biến thể N>=2, tập đánh giá giảm từ 90 xuống 85 nhóm; mẫu số được lưu trong bảng.

Gói bằng chứng lịch sử của lab được giữ trong `legacy/IAM302t_HuongB_RF_Final_Source_Evidence.zip`; kết quả hiện hành dùng cho báo cáo nằm trong `lab/results/`.
