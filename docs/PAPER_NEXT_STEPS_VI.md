# Bước tiếp theo để phát triển thành paper

Cập nhật 04/11/2026, sau khi đối chiếu gói thực chạy trên VM. Mục tiêu là một bài audit có đóng góp rõ, bằng chứng đủ và phạm vi kết luận khớp dữ liệu. Thí nghiệm RF 5 seed đã hoàn tất 30/30 cấu hình, được kiểm chứng và đưa vào bài. Các mục dưới đây phân biệt phần đã xong với bước chuẩn bị gửi paper.

## 1. Ba luận điểm cần bảo vệ

| Luận điểm | Bằng chứng hiện có | Việc cần củng cố |
|---|---|---|
| Bỏ explicit type chưa loại hết thông tin type | Cây sâu 3 dự đoán PTR từ TTL, accuracy held-out 98,14%; các ablation RF/LR | Phân biệt khả năng phục hồi thông tin với kết luận nhân quả; đối chiếu các bài DNS đã dùng TTL/type |
| Hiệu ứng ablation phụ thuộc mô hình và split | RF G2 sụp, G1/G2 đảo chiều khi bỏ name statistics; refits khớp; paths và cohort probe | Đã kiểm tra 5 seed trên cả 3 fold và công bố mọi kết quả; tiếp tục định vị đóng góp so với công trình gần nhất |
| Biểu diễn train/test CTU khác nhau | Originals có checksum đúng; tất cả train không dot; dot coefficient=0 và bỏ DOTS không đổi dự đoán | Đặt phạm vi release/pipeline rõ; chưa có checkpoint gốc để định lượng ảnh hưởng lên MC-CNN |

Các kết quả là những case study có thể kiểm chứng. Chưa có cơ sở dùng từ “đầu tiên” hoặc khẳng định đã bao phủ mọi nghiên cứu DNS tunneling.

## 2. Đối chiếu nghiên cứu liên quan bước đầu

| Công trình / nguồn chính | Điểm liên quan | Cách bài này cần phân biệt đóng góp |
|---|---|---|
| Arp et al., USENIX Security 2022, [Dos and Don’ts](https://www.usenix.org/conference/usenixsecurity22/presentation/arp) | Hệ thống hóa pitfalls của ML bảo mật | Đóng góp dự kiến là bằng chứng DNS cụ thể và quy trình đo residual information, không phải khái niệm chung về pitfalls |
| Zhao et al., TOSEM 2021, [sample duplication](https://research.monash.edu/en/publications/on-the-impact-of-sample-duplication-in-machine-learning-based-and/) | Tác động của duplication cần đo theo mô hình/tác vụ | Định lượng duplicates và giữ exact-vector control; không suy điểm bị thổi phồng từ số dòng trùng |
| Pendlebury et al., USENIX Security 2019, [TESSERACT](https://www.usenix.org/conference/usenixsecurity19/presentation/pendlebury) | Split phải phản ánh mục tiêu tổng quát hóa | Coarse token không tự trở thành domain/family/time holdout; seed cũng không tạo population mới |
| Engelen et al., SPW 2021, [CICIDS2017 audit](https://intrusion-detection.distrinet-research.be/WTMC2021/) | Audit phải truy pipeline xây dữ liệu và nhãn | Không gán lỗi CICIDS2017 cho CIC DNS; phân biệt bản CSV thứ ba và release gốc |
| Nadler et al., Computers & Security 2019, [low-throughput exfiltration](https://doi.org/10.1016/j.cose.2018.09.006) | Bài toán low-throughput cần đặt đúng môi trường đánh giá | Bài hiện tại audit các đầu vào đã có, chưa là đánh giá detector trên mọi kiểu exfiltration thực tế |
| Mahdavifar et al., ICCNS 2021, [CIC hybrid](https://doi.org/10.1145/3507509.3507520), [official release](https://www.unb.ca/cic/datasets/dns-exf-2021.html) | Hệ thống hai tầng và nhiều loại dữ liệu | Baseline một tầng trên CSV không tái lập đầy đủ stateless-first/gating; không lấy hiệu hai điểm làm shortcut inflation |
| Palau et al., ASAI 2019, [MC-CNN](https://sedici.unlp.edu.ar/handle/10915/87859), [release](https://zenodo.org/records/6508640) | Công trình gắn với release CTU ba công cụ | Chứng minh mismatch trong file phát hành và trace preprocessing; tác động lên checkpoint gốc vẫn chưa đo được |
| Palau et al., 2020, [five-tool follow-up](https://arxiv.org/abs/2006.06122) | Mô tả bộ dữ liệu mới với năm công cụ | Không tự động gán artifact của release 2019 cho dữ liệu khác |

Bảng này là định vị ban đầu, chưa thay thế rà soát toàn văn có hệ thống. Cần tiếp tục tìm nghiên cứu về artifact/proxy trong DNS datasets để kiểm tra mức độ mới của từng phát hiện.

## 3. Đã hoàn tất: RF qua 5 seed cố định

Đã nhận và kiểm chứng toàn bộ 30 cấu hình: 5 seed × 3 frozen folds × FULL/NO_DOMAIN. Kế hoạch, source/data/split hashes, môi trường VM, nhãn thật, predicted labels và scores đều được đối chiếu. Cả 6 baseline seed 42 khớp nhãn từng dòng; 6 summaries và 15 paired differences được tính lại độc lập.

| Fold | Đặc trưng | F1 nhỏ nhất | F1 trung vị | F1 lớn nhất |
|---|---|---:|---:|---:|
| GROUP_1 | FULL | 0.886002 | 0.886325 | 0.886487 |
| GROUP_1 | Bỏ 14 name statistics | 0.000000 | 0.001576 | 0.044275 |
| GROUP_2 | FULL | 0.000381 | 0.000381 | 0.004641 |
| GROUP_2 | Bỏ 14 name statistics | 0.775907 | 0.775907 | 0.775950 |
| GROUP_3 | FULL | 0.677327 | 0.687893 | 0.688258 |
| GROUP_3 | Bỏ 14 name statistics | 0.333996 | 0.333996 | 0.334007 |

Chiều tác động FULL-minus-no-name giữ dấu tại mọi seed: dương trên GROUP 1/3, âm trên GROUP 2. GROUP-1 no-name ở seed 2026 có F1 0,044275, lớn hơn các seed còn lại nhưng vẫn rất thấp. GROUP-2 no-name đạt F1 khoảng 0,7759 cùng FPR 28,11–28,13%; không diễn giải đây là một detector đã sửa tốt.

Kết quả hỗ trợ tính lặp lại của fold-specific response dưới forest randomness. Các seed dùng cùng test rows, không tạo thêm capture độc lập, confidence interval cho deployment, hoặc registrable-domain holdout. Phân tích path/prototype chi tiết vẫn thuộc seed 42.

Đọc `PAPER_RF_SEED_REVIEW_VI.md` để xem biên bản; dữ liệu đầy đủ ở `results/paper_rf_seeds/`. Bài chính giữ 2 bảng + 2 hình; whiskers RF của hình cơ chế thể hiện min–max 5 seed. Phụ lục có cả 30 trường hợp và hình phân bố seed.

Dùng `source/verify_rf_seed_check.py` trong bản nguồn mới để kiểm tra các kết quả đã lưu. Bước hiện tại đã hoàn tất, không còn là thí nghiệm đang chờ chạy.

## 4. Chốt nơi nộp sau khi xác định phạm vi

Hướng làm việc hiện tại phù hợp để chuẩn bị một focused audit paper, ưu tiên xem xét workshop/short-paper track có chủ đề network measurement, dataset quality hoặc ML security. Việc chọn venue cần biết hạn nộp, yêu cầu của thầy/trường và khả năng chi phí/tham dự.

Đã kiểm tra CFP WTMC 2026: chủ đề có liên quan và có short/regular/long-paper track, nhưng deadline **13/07/2026 đã qua**, nên không phải lựa chọn đang nhận bài ngày 04/11/2026. Nguồn: [WTMC](https://wtmc.info/index.html), [IEEE Security calendar](https://www.ieee-security.org/Calendar/cfps/cfp-WTMC2026.html). Chưa xác minh được CFP WTMC 2027; không gán lịch dự kiến thành deadline thật.

USENIX Security 2027 có tiêu chí originality, rigor và open-science; đây là nguồn tham khảo về tiêu chuẩn, chưa phải venue được chọn cho dự án: [CFP](https://www.usenix.org/conference/usenixsecurity27/call-for-papers).

Sau khi chốt venue, kiểm tra đúng template, page limit, ẩn danh, link artifact, AI disclosure và quy định submission. Bản nộp môn học có tên tác giả/giảng viên và repository public cần được điều chỉnh nếu venue yêu cầu ẩn danh.

## 5. Tiêu chí chuyển sang bản nộp

1. Hoàn tất đọc/đối chiếu công trình gần nhất và mô tả được đóng góp riêng.
2. **Đã hoàn tất:** đủ 30 cấu hình seed, kiểm tra toàn bộ và cập nhật bài theo kết quả thật.
3. Chốt phạm vi CIC coarse-token và CTU release; không nâng thành tuyên bố vượt dữ liệu.
4. Repository/anonymous artifact truy cập và tái lập được theo quy định nơi nộp.
5. Tất cả tác giả đọc, hiểu và duyệt nội dung, citation và khai báo AI trước khi gửi.

Bản hiện tại hoàn tất tái lập, đối chiếu dữ liệu và thí nghiệm RF qua 5 seed. Việc rà soát novelty, chốt venue, hoàn tất repository/anonymous artifact và duyệt tác giả vẫn cần tiếp tục.
