> Hồ sơ bản nộp 01/11/2026. Nhận xét cuối và chẩn đoán bổ sung ngày 03/11 nằm trong `PHAN_HOI_NHAN_XET_CUOI_VI.md`, `CTU_PIPELINE_TRACE.md` và `results/revision_v2/`.

# Đối chiếu kết quả thực chạy trên VM — 01/11/2026

Python của VM là 3.12.16. File split được tạo ở môi trường tham chiếu Python 3.12.14 và giữ nguyên khi tái hiện trên VM. SHA-256 dữ liệu CIC và file split khớp; metadata của hai giai đoạn được lưu riêng.

- 25 cấu hình LR và 25 cấu hình RF: kiểm tra lại confusion matrix/F1/FPR từ nhãn gốc, chỉ số test và dự đoán từng dòng; cả 50 khớp bản tham chiếu.
- Kết quả CTU, auxiliary PTR/TTL, RF 41 cột, LAB baseline, 24 cấu hình missing values và graph ablation: các trị số đối chiếu khớp.
- Log thực chạy theo bước ở logs/01_* đến logs/05_*. Log tham chiếu cũ nằm trong legacy/reference_logs/; log biên dịch PDF hiện hành là logs/latex_build_vm_final.log.
- Gói nhận từ VM được giữ nguyên tại evidence/IAM302t_KetQua_VM.zip. Đối chiếu chi tiết lưu tại results/VM_RECEIPT_VALIDATION.json.
- requirements-lock.txt khóa đủ 18 gói từ VM_ENVIRONMENT.json. Source các thí nghiệm chính giữ nguyên so với bản đã chạy trên VM.

PDF dùng bảng và hình đã sinh từ kết quả của VM. Việc biên dịch PDF được thực hiện riêng; nó không huấn luyện lại mô hình.

Phần cần dữ liệu bổ sung vẫn gồm tái lập đúng hybrid CIC và public source-IP audit với PCAP có nhãn benign/attack. URL kho mã công khai cần địa chỉ kho thực tế. Các phần này được liệt kê trong docs/DOI_CHIEU_PHUONG_PHAP_GOC_VI.md.
