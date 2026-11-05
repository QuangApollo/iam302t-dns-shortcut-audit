# CTU: truy vết biểu diễn và phạm vi đối chiếu công trình đã công bố

Cập nhật 03/11/2026. Kết quả máy đọc được: `results/revision_v2/ctu_source_trace.json`, `ctu_original_representation.csv`, `ctu_control_metadata.json`.

## 1. Nguồn đã kiểm tra

- Release: https://zenodo.org/records/6508640 (hai file `train_combined_multiclass.csv.gz`, `test_combined_multiclass.csv.gz`). Hai bản tải lại khớp MD5 công bố và SHA-256 đã lưu từ bản nộp trước.
- Bài 2019: Palau et al., *Detecting DNS Threats: A Deep Learning Model to Rule Them All*, ASAI/JAIIO 48, tr.90–101. Bản gốc: https://sedici.unlp.edu.ar/handle/10915/87859.
- Mã tác giả có liên hệ: https://github.com/harpomaxx/deepseq, commit `769e3466f90173b663aa1fe3008e7a70295fbdfd`. Đã kiểm tra bốn file `preprocess.R`, `deepseq_classifier.R`, `config.R`, `model_mc_cnn_asai.R`; hash và vị trí dòng lưu trong JSON.
- Bài tiếp theo năm 2020: https://arxiv.org/abs/2006.06122v2. Bài này giới thiệu **bộ dữ liệu mới với năm công cụ**, không được tự động gộp với release ba công cụ đang audit.

## 2. Những gì xác minh được

| Bước | Bằng chứng | Kết luận |
|---|---|---|
| Release gốc | Mọi chuỗi train của cả ba lớp không chứa dấu chấm; raw test chứa dấu chấm ở 236.027 benign, 383.071 DGA, 1.559 tunnel | Khác biệt đã có trước class filtering và feature extraction của nhóm |
| Chuẩn hóa lexical | Trim, lowercase, bỏ dấu chấm cuối; benign test có 236.025 chuỗi còn dấu chấm | Hai chuỗi chỉ khác ở root dot cuối; không phải mâu thuẫn giữa hai thống kê |
| Hình học đặc trưng | Tất cả 950.547 train binary có length = max-label-length = mean-label-length; 237.584/237.631 test vi phạm đẳng thức | Biểu diễn chung của nhiều đặc trưng đã thay đổi, không chỉ DOTS |
| Bỏ DOTS | Hệ số DOTS LR8 = 0; LR7 bỏ DOTS cho cùng toàn bộ dự đoán với LR8 trong cả hai biểu diễn test | Bỏ một cột không sửa được representation mismatch |
| Đối chiếu bài 2019 | Support ba lớp tại Table 3 khớp số dòng test của release | Có căn cứ truy vết pipeline này; không đồng nghĩa đã tái dựng chính xác run gốc |
| Mã tiền xử lý | Tokenize theo ký tự, padding/truncation ở cuối, mặc định maxlen 45; hàm được kiểm tra không bỏ suffix | Truncation này không tự động khôi phục đơn vị train/test giống nhau |
| Kiểm tra first-45 | Dấu chấm vẫn nằm trong 45 ký tự đầu ở 236.027 normal, 383.071 DGA và 1.257 tunnel raw test; train không có | Artifact còn hiện diện dưới quy ước độ dài đã kiểm tra |

Bài 2019 mô tả split 70/30 trong phần văn bản, còn số lớp trong file release tương ứng xấp xỉ 80/20. Bản sửa ghi nhận sự khác biệt này ở phụ lục; không suy diễn support khớp thành toàn bộ quy trình khớp.

## 3. Điều chưa được xác minh

Chưa có bằng chứng xác định đầy đủ vocabulary, cấu hình run năm 2019, checkpoint huấn luyện và trace đánh giá tương ứng. Cấu hình trong repository có các lựa chọn dữ liệu/vocabulary khác nhau. Kiểm tra first-45 chỉ đo khả năng artifact còn xuất hiện ở đầu vào; **không phải chạy lại pipeline R hay tính lại điểm MC-CNN**.

Vì vậy bản sửa xác nhận artifact của release và hậu quả lên các baseline lexical của nhóm; yêu cầu các đánh giá dùng split này phải kiểm tra/đồng nhất biểu diễn. Bản sửa không khẳng định mọi kết quả CTU đã công bố đều vô nghĩa, cũng không gán artifact của release này cho bộ dữ liệu mới năm 2020.

## 4. Tái lập

```bash
.venv312/bin/python source/prepare_ctu.py --download
.venv312/bin/python source/revision_v2_ctu.py --originals data/ctu/raw
.venv312/bin/python source/trace_ctu_source.py --download
```

Các lệnh tải dữ liệu gốc và mã công khai cần Internet. Các số liệu và hash đã kèm sẵn; `source/verify_revision.py` kiểm tra bằng chứng đã lưu mà không tải lại hay huấn luyện lại.
