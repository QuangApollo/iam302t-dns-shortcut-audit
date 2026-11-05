> Hồ sơ bản nộp 01/11/2026. Nhận xét cuối và chẩn đoán bổ sung ngày 03/11 nằm trong `PHAN_HOI_NHAN_XET_CUOI_VI.md`, `CTU_PIPELINE_TRACE.md` và `results/revision_v2/`.

# Đối chiếu góp ý giảng viên sau lần sửa 01/11/2026

| Góp ý | Việc đã thực hiện | Bằng chứng | Phạm vi còn lại |
|---|---|---|---|
| M1 — Lab cho phép suy ra nhãn từ IP/QTYPE/domain | Giữ các luật chẩn đoán, định vị lại đóng góp là kiểm toán, không kết luận Graph tổng quát hóa từ F1=1 | lab/results/08_posthoc_simple_rules.csv; báo cáo phần Laboratory Checks | Muốn giữ giả thuyết phát hiện gốc cần thu thập dữ liệu đối chứng như Hướng A |
| M2 — Graph và các cấu hình bỏ type còn proxy | Bổ sung script sinh ba ablation đơn; kiểm tra trực tiếp PTR có thể dự đoán từ TTL; thêm NO_QTYPE_TTL và NO_BOTH_TTL | lab/results/03_feature_ablation.csv; results/qtype_proxy_results.csv; results/lr_results.csv; results/rf_results.csv | Việc bỏ cột được chỉ định chưa bảo đảm loại mọi proxy; dữ liệu đối chứng mới cần cho kết luận nhân quả |
| M3 — Đồ thị ít client, chưa thử chậm/phân tán | Bỏ kết luận phát hiện chậm/phân tán; dùng lab như trường hợp minh họa kiểm toán | Mục tiêu/RQ và phần giới hạn báo cáo | Chưa có thí nghiệm graph đa client hoặc tunnel chậm mới |
| M4 — N độc lập nhỏ, so sánh thiếu ổn định | Chạy cả LR/RF trên đủ 3 group folds cố định; thêm exact-vector holdout; phân tích hai token chứa 92,69% attack | results/model_summary.csv; results/fold_dominant_groups.csv; splits/ | SLD không tương đương tool/session; chưa tăng số phiên tunnel độc lập trong lab |
| M5 — FP và imputation | Replay đủ 4 cấu hình × 6 chiến lược; median làm HYBRID FP 6→4; kiểm tra 114 SERVFAIL và 96 response chậm đều ở normal | lab/results/02_missing_value_sensitivity.csv; lab/results/06_dns_response_by_class.csv | Giữ kết luận đúng theo phép đo; không quy toàn bộ FP cho một nguyên nhân |
| M6 — Dữ liệu công khai, related work, kết quả công bố | Tải lại CTU và xác minh checksum; bổ sung trích nguồn mirror CIC; kiểm toán duplicate/conflicting vectors; RF 41 cột là baseline tham khảo gần hơn; bổ sung Nadler và giữ trích dẫn chuẩn | results/ctu_preparation.json; results/dataset_audit.json; results/reference_inventory_results.csv; tài liệu tham khảo | Chưa tái lập hybrid hai tầng CIC hoặc chứng minh tác động lên chính điểm 99,97% công bố; public IP còn thiếu đối chứng |
| Trình bày và mã nguồn | Báo cáo tập trung vào kết quả kiểm toán; bỏ câu hậu trường soạn bài; bảng/hình lấy từ CSV; kết quả hiện hành trong results/, bằng chứng lịch sử trong legacy/ | report/; source/build_report_assets.py | URL kho mã công khai cần được tạo/cung cấp trước khi thêm vào báo cáo |

Các phép kiểm tra mới làm mạnh hơn bằng chứng về phụ thuộc đánh giá. Kết quả là phát hiện phương pháp trên những nguồn đã mô tả, không phải xác nhận trước về điểm chấm hoặc khả năng công bố.
