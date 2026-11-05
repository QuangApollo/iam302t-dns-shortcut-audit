# Phản hồi nhận xét cuối của giảng viên — Nhóm 3, IA2007

**Bản sửa:** 05/11/2026; xác minh kho mã công khai, giữ kết quả thực chạy VM.  
**Tên bài:** *Auditing Shortcut Dependencies in DNS Tunneling: Residual Information across Models and Splits*.  
**Thành viên:** Mai Chí Thành; Đỗ Quang Thuận; Nguyễn Lê Quốc Bảo; Đặng Nguyễn Phương Thảo.  
**Giảng viên:** Mai Hoàng Đỉnh.

Nhóm đã sửa cấu trúc bài quanh luận điểm: **bỏ một cột không đồng nghĩa đã bỏ thông tin cột đó mang; hiệu ứng còn phụ thuộc mô hình và cách chia tập**. CIC là trường hợp chính, CTU là phát hiện về biểu diễn, LAB hỗ trợ diễn giải. Các bảng chi tiết được chuyển sang phụ lục.

| Nhận xét | Nội dung đã sửa | Vị trí / bằng chứng |
|---|---|---|
| M1 — Chốt thông điệp | Viết lại tiêu đề, abstract, ba câu hỏi nghiên cứu, kết luận; kết nối proxy TTL, RF/LR, CTU bằng vấn đề thông tin còn sót sau ablation | Bài chính I, IV, V, VIII; Table I |
| M2 — Giải thích RF GROUP 2 | Chạy lại 8 cấu hình RF/LR × G1/G2 × FULL/NO_DOMAIN, khớp toàn bộ dự đoán VM; thêm feature-shift, đường đi thật của cây, score decomposition và input-sensitivity trên toàn test | Bài chính IV-B, Figure 1; `results/revision_v2/`; phụ lục IV |
| M3 — Ý nghĩa SLD token | Đổi cách diễn giải thành **coarse-token sensitivity**. Nêu rõ token là chuỗi chuẩn hóa dùng để nhóm, không phải hash hoặc registrable domain đã xác thực | Bài chính III-B, VII; inventory và giới hạn trong phụ lục |
| M4 — Khung audit chung | Table I liên kết source → unit → artifact → test → valid inference; không xếp hạng F1 giữa các nguồn khác đơn vị | Bài chính Table I và VI |
| M5 — CTU mismatch | Nâng thành kết quả chính; xác minh lại originals, kiểm tra cả DGA, thêm identity length/label-length, bỏ DOTS, truy vết bài 2019 và mã tác giả ở commit cố định | Bài chính V, Figure 2; `docs/CTU_PIPELINE_TRACE.md`; phụ lục VI |
| Giảm bảng và chuỗi số | Bài chính còn 4 displays: 2 bảng + 2 hình. Chuyển full folds, ablations, LAB và CTU controls sang phụ lục; rút Korving xuống coverage row và diễn giải ngắn | Bài chính 5 trang; phụ lục số liệu đầy đủ |
| Related work | Thêm Arp 2022, Zhao 2021, TESSERACT 2019, Engelen 2021; đối chiếu nguồn chính thức/tác giả | Bài chính II và References |
| Khai báo AI | Thêm công cụ, loại hỗ trợ, nguồn số liệu thực chạy và trách nhiệm của tác giả | Bài chính VII, phụ lục cuối |
| Kho mã công khai | Đã công khai và xác minh đủ 255/255 file, gồm 95 NPZ. Hai PDF ghi URL thật; có hướng dẫn khôi phục dữ liệu đúng checksum và verify dự đoán đã lưu | https://github.com/QuangApollo/iam302t-dns-shortcut-audit; `CODE_AVAILABILITY.json` ghi commit và phạm vi xác minh; `docs/XUAT_BAN_GITHUB_VI.md` |

## Đính chính kỹ thuật quan trọng ở M2

Cách giải thích “RF trực tiếp học SLD=192 thì attack” chưa phù hợp với pipeline chính: `sld` không nằm trong 43 đầu vào RF/LR, chỉ dùng `GroupKFold`. Thay toàn bộ `sld` mà giữ indices không đổi khiến ma trận đầu vào giữ nguyên. RF 41-field reference control là một pipeline riêng và được phân biệt rõ.

Dữ liệu thực cho thấy GROUP 2 đổi phân bố name statistics. Trung vị entropy của attack đổi từ 2,675 (train) xuống 2,054 (test); `len` từ 14 xuống 11; `subdomain_length` từ 10 xuống 7. Trên một input bị bỏ sót phổ biến, các nhánh `FQDN_count`, entropy và độ dài kéo score RF xuống dưới 0,5, dù nhánh PTR ban đầu tăng score. Việc bỏ name statistics đảo chiều nhạy cảm giữa G1 và G2. Vì vậy bài giải thích bằng **ngưỡng trên numeric proxies và phân bố quần thể**, thay vì gán một luật literal token không có trong model.

Probe thay 14 name inputs bằng median attack của train tăng median score RF của attack G2 từ 0,333 lên 0,806. Cùng phép thay cũng làm khoảng 29% benign bị dự đoán dương tính, nên nhóm dùng nó để kiểm tra feature reliance, không quảng bá thành detector cải thiện. Phụ lục công bố cả tác động lên benign.

## Phần M3 chưa thể thay bằng một thí nghiệm domain thật

CSV có các thống kê engineered và token `sld`, không có FQDN đầy đủ hay ánh xạ về capture/transaction gốc. Public Suffix List không thể khôi phục registrable domain thật từ `192`/`224`. Nhóm giữ indices cũ để bảo toàn đối chiếu, hạ đúng mức kết luận của GROUP, và không tạo một split “domain-disjoint” giả. Muốn làm thí nghiệm mạnh hơn cần raw query names và lineage xác minh được.

## Phạm vi kết luận CTU

Nhóm xác nhận mismatch tồn tại trong originals có checksum đúng và còn tồn tại dưới phép cắt 45 ký tự đầu của mã đã kiểm tra. Tuy nhiên, run configuration và checkpoint MC-CNN gốc chưa xác định được, nên chưa thể tính mức ảnh hưởng lên điểm công bố. Bài 2020 dùng bộ mới với năm công cụ; không được tự động gán cùng artifact. Phụ lục lưu giới hạn này tập trung, tránh lặp rào đón trong mỗi đoạn.

## Kiểm tra số liệu

- 50 cấu hình CIC gốc: tính lại chỉ số từ prediction arrays và nhãn gốc.
- 8 refits cơ chế: predictions khớp VM từng dòng.
- Cohort sensitivity: lưu và tính lại mean/median/fraction từ score từng dòng cho cả benign và attack.
- CTU: 4 confusion matrices; LR8/LR7 khớp prediction arrays; 2 original downloads khớp publisher MD5 và SHA-256.
- Dataset/split checksum giữ nguyên; mã/script, môi trường và log mới được ghi riêng, không đổi danh tính kết quả VM gốc.

**Trước khi nộp lại:** tác giả đọc và chịu trách nhiệm nội dung, đặc biệt AI disclosure; dùng hai PDF mới có URL kho mã đã xác minh. Gửi kèm gói nguồn đầy đủ qua LMS để thầy có mã, dữ liệu, mọi saved prediction và log VM gốc. Kho GitHub cũng đã chứa đủ 95 NPZ của gói công khai.

## Bằng chứng chạy lại trên VM ngày 04/11

Các chẩn đoán mới đã thực chạy trên VM của nhóm, thay cho việc chỉ kiểm tra file kết quả kèm sẵn. Gói nhận được gồm 130 file và 6 log thực thi. Đối chiếu 15 script, frozen split và 18 package đều khớp. Tính lại 50 cấu hình gốc, 8 refits, 8 cohort summaries và 4 CTU controls đạt. Nhãn dự đoán không đổi so với bản tham chiếu; một số score LR chênh tối đa 0,005063 giữa hai lần thực thi. Nguyên nhân số học chưa được cô lập. Bảng/hình được sinh lại từ kết quả VM; receipt ghi cả khác biệt này.

Gói cơ chế này hoàn tất bước tái lập. Phần kiểm tra RF qua nhiều seed đã được bổ sung và kiểm chứng ở mục dưới; chưa có nhiều capture độc lập.

## Bổ sung kiểm tra RF qua 5 seed — 04/11/2026

Đã hoàn tất 30 fit trên cả ba coarse-token folds, hai feature sets và năm seed cố định. Tái tính toàn bộ confusion matrices, xác nhận sáu baseline seed 42 và 15 so sánh theo cặp. Ablation reversal giữ cùng chiều tại mọi seed trên từng fold; GROUP-2 FULL F1 0,000381–0,004641, còn no-name khoảng 0,7759 với FPR khoảng 28,1%. Bài chính và phụ lục đã cập nhật; đây là độ ổn định stochastic estimator trên cùng test rows, không phải năm capture độc lập. Chi tiết ở `PAPER_RF_SEED_REVIEW_VI.md`.
