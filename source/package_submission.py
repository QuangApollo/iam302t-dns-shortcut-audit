#!/usr/bin/env python3
"""Build the complete revision, compact public repo, and isolated Overleaf ZIPs."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BUILD_DATE = (2026, 11, 4, 0, 0, 0)
TEMP_SUFFIXES = {'.aux', '.out', '.fls', '.fdb_latexmk', '.xdv', '.pyc', '.part', '.partial', '.synctex.gz'}


def eligible(path):
    relative = path.relative_to(ROOT)
    if not path.is_file() or any(part in ['__pycache__', '.git'] or part.startswith('.venv') for part in relative.parts):
        return False
    if path.name.startswith('.') and path.name != '.gitignore':
        return False
    if path.suffix in TEMP_SUFFIXES or path.name.endswith('.synctex.gz'):
        return False
    if relative.parts[0] == 'report' and path.suffix == '.log':
        return False
    if relative.as_posix().startswith(('data/ctu/raw/', 'data/ctu/associated_source/')):
        return False
    return True


def manifest(payload):
    return ''.join(hashlib.sha256(raw).hexdigest() + '  ' + name + '\n'
                   for name, raw in sorted(payload.items())).encode('utf-8')


def write_zip(path, payload, prefix=''):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, raw in sorted(payload.items()):
            entry = zipfile.ZipInfo(prefix + name, BUILD_DATE)
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = ((0o100755 if name.endswith('.sh') else 0o100644) << 16)
            archive.writestr(entry, raw)
    raw = buffer.getvalue()
    path.write_bytes(raw)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        assert archive.testzip() is None
    return {'name': path.name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def main(output):
    output = output.resolve()
    if output.is_relative_to(ROOT):
        raise SystemExit('Use an output folder outside the project tree.')
    output.mkdir(parents=True, exist_ok=True)
    main_tex = (ROOT / 'report/main.tex').read_text()
    assert len(re.findall(r'\\begin\{table\*?\}', main_tex)) == 2
    assert len(re.findall(r'\\begin\{figure\*?\}', main_tex)) == 2
    status = json.loads((ROOT / 'CODE_AVAILABILITY.json').read_text())
    report_qa = json.loads((ROOT / 'results/revision_v2/report_qa.json').read_text())
    main_pages, supplement_pages = report_qa['main_pages'], report_qa['supplement_pages']
    payload = {p.relative_to(ROOT).as_posix(): p.read_bytes()
               for p in sorted(ROOT.rglob('*')) if eligible(p) and p.name != 'MANIFEST_SHA256.txt'}
    payload['MANIFEST_SHA256.txt'] = manifest(payload)
    (ROOT / 'MANIFEST_SHA256.txt').write_bytes(payload['MANIFEST_SHA256.txt'])
    checks = []
    source_name = '02_IAM302t_Nhom3_MaNguon_DuLieu_BangChung.zip'
    checks.append(write_zip(output / source_name, payload, 'IAM302t_HuongB_Revised/'))
    overleaf = {name.removeprefix('report/'): raw for name, raw in payload.items()
                if name.startswith('report/') and not name.startswith('report/archive/')
                and (name.endswith(('.tex', '.cls', '.ttf', '.png')) or name.startswith('report/fonts/')
                     or name.startswith('report/figures/') or name == 'report/README_OVERLEAF_VI.md')}
    # Reports themselves are separate deliverables; Overleaf contains sources/assets only.
    overleaf = {name: raw for name, raw in overleaf.items()
                if name not in ['IAM302t_HuongB_Revised_IEEE.pdf', 'IAM302t_HuongB_Supplement.pdf']}
    overleaf['MANIFEST_SHA256.txt'] = manifest(overleaf)
    overleaf_name = 'IAM302t_HuongB_Revised_Overleaf.zip'
    checks.append(write_zip(output / overleaf_name, overleaf))
    public = {name: raw for name, raw in payload.items()
              if not name.startswith(('data/', 'legacy/', 'evidence/', 'logs/', 'report/archive/'))
              and name != 'MANIFEST_SHA256.txt'}
    public['MANIFEST_SHA256.txt'] = manifest(public)
    public_name = 'IAM302t_Nhom3_GitHub_Ready.zip'
    checks.append(write_zip(output / public_name, public, 'iam302t-dns-shortcut-audit/'))
    reports = {
        'IAM302t_HuongB_Revised_IEEE.pdf': ROOT / 'report/IAM302t_HuongB_Revised_IEEE.pdf',
        'IAM302t_HuongB_Supplement.pdf': ROOT / 'report/IAM302t_HuongB_Supplement.pdf',
        'PHAN_HOI_NHAN_XET_CUOI_VI.md': ROOT / 'docs/PHAN_HOI_NHAN_XET_CUOI_VI.md',
        'HUONG_DAN_TUNG_BUOC_VI.md': ROOT / 'HUONG_DAN_TAI_LAP_VI.md',
    }
    for name, path in reports.items():
        (output / name).write_bytes(path.read_bytes())
    availability = ('Kho mã công khai đã được xác minh: ' + str(status['url'])
                    if status['status'] == 'public_verified' else
                    'CHƯA HOÀN TẤT URL kho mã công khai: cần đăng bằng tài khoản GitHub của tác giả và gắn URL thật vào báo cáo. Mã đã chuẩn bị trong gói GitHub Ready.')
    readme = f'''# Bộ sửa theo nhận xét cuối — Nhóm 3, IA2007

Ngày 04/11/2026, bản sửa 4; đã đối chiếu gói VM và đủ 30 cấu hình RF seed. Giảng viên: Mai Hoàng Đỉnh. Thành viên: Mai Chí Thành; Đỗ Quang Thuận; Nguyễn Lê Quốc Bảo; Đặng Nguyễn Phương Thảo.

## File hiện hành

| File | Nội dung |
|---|---|
| `01_IAM302t_Nhom3_BaoCao_Sua.pdf` | Bài chính {main_pages} trang; 2 bảng + 2 hình; khai báo AI và 16 tham chiếu |
| `02_IAM302t_Nhom3_PhuLuc.pdf` | Phụ lục {supplement_pages} trang; đủ fold/ablation/provenance, cơ chế và 30 cấu hình seed |
| `{source_name}` | Mã, dữ liệu, indices cố định, predictions, log VM và chẩn đoán mới |
| `03_IAM302t_Nhom3_Overleaf.zip` | Nguồn hai báo cáo; chọn XeLaTeX, compile main.tex/supplement.tex |
| `04_PhanHoi_NhanXet_Cuoi.md` | Phản hồi từng nhận xét, kèm đính chính SLD chỉ dùng chia nhóm |
| `05_HuongDan_TaiLap.md` | Cài môi trường và kiểm tra; dùng Python môi trường ảo trực tiếp |
| `{public_name}` | Repository gọn sẵn để đăng; có script tải dữ liệu đúng checksum |
| `06_KeHoach_BuocTiep_Paper.md` | Tiến độ nghiên cứu, giới hạn và bước chuẩn bị gửi paper |
| `07_BienBan_KiemTra_VM.md` | Đối chiếu gói nhận được, nhãn dự đoán và khác biệt score |
| `08_KiemTra_RF_5Seed.md` | Đủ kết quả 30 cấu hình, kiểm chứng và phạm vi diễn giải |
| `MANIFEST_SHA256.txt` | Checksum các file trong bộ này |

## Trạng thái cần biết trước khi nộp lại

{availability}

Các tác giả cần đọc lại và chịu trách nhiệm nội dung/AI disclosure trước khi gửi thầy. Không cần huấn luyện lại để thêm link mã. Sau khi có URL, xem `docs/XUAT_BAN_GITHUB_VI.md` trong gói nguồn, compile lại hai PDF và chạy `source/package_submission.py` để tạo lại bộ nộp.

## Kết quả kiểm chứng

50 cấu hình CIC gốc được tái tính từ prediction arrays; 8 refits cơ chế khớp VM; cohort probe kiểm tra từ score từng dòng; 4 CTU controls khớp confusion matrices; originals CTU khớp MD5/SHA-256. Chi tiết ở `results/revision_v2/verification.json` và `report_qa.json` trong gói nguồn.

Đã kiểm chứng đủ 30 cấu hình RF qua 5 seed: sáu baseline seed 42 khớp, sáu summaries và 15 paired differences được tái tính. Chiều ablation giữ nguyên tại mọi seed trên từng fold. Receipt riêng ở `results/paper_rf_seeds/verification.json`; đây là biến thiên mô hình trên cùng test rows, không phải nhiều capture độc lập.

GROUP là độ nhạy theo token thô, không phải registrable-domain holdout. Probe thay name statistics là phép kiểm tra đầu vào nhân tạo, không phải detector mới. Phát hiện CTU là artifact của release; chưa tái lập checkpoint MC-CNN gốc.
'''
    (output / 'DOC_TRUOC_KHI_NOP.md').write_text(readme)
    kit = {
        '01_IAM302t_Nhom3_BaoCao_Sua.pdf': (output / 'IAM302t_HuongB_Revised_IEEE.pdf').read_bytes(),
        '02_IAM302t_Nhom3_PhuLuc.pdf': (output / 'IAM302t_HuongB_Supplement.pdf').read_bytes(),
        source_name: (output / source_name).read_bytes(),
        '03_IAM302t_Nhom3_Overleaf.zip': (output / overleaf_name).read_bytes(),
        '04_PhanHoi_NhanXet_Cuoi.md': (output / 'PHAN_HOI_NHAN_XET_CUOI_VI.md').read_bytes(),
        '05_HuongDan_TaiLap.md': (output / 'HUONG_DAN_TUNG_BUOC_VI.md').read_bytes(),
        public_name: (output / public_name).read_bytes(),
        'DOC_TRUOC_KHI_NOP.md': readme.encode('utf-8'),
        '06_KeHoach_BuocTiep_Paper.md': (ROOT / 'docs/PAPER_NEXT_STEPS_VI.md').read_bytes(),
        '07_BienBan_KiemTra_VM.md': (ROOT / 'docs/PAPER_VM_REVIEW_VI.md').read_bytes(),
        '08_KiemTra_RF_5Seed.md': (ROOT / 'docs/PAPER_RF_SEED_REVIEW_VI.md').read_bytes(),
    }
    kit['MANIFEST_SHA256.txt'] = manifest(kit)
    checks.append(write_zip(output / 'IAM302t_Nhom3_BO_NOP.zip', kit, 'IAM302t_Nhom3_BanSua_2026-11-04/'))
    (output / 'IAM302t_HuongB_TAI_LAI_TRON_BO.zip').write_bytes((output / 'IAM302t_Nhom3_BO_NOP.zip').read_bytes())
    (output / 'PACKAGE_CHECKS.json').write_text(json.dumps({'archives': checks,
        'source_files': len(payload), 'overleaf_files': len(overleaf), 'public_repo_files': len(public),
        'availability': status, 'all_zip_crc_passed': True}, indent=2) + '\n')
    print(json.dumps({'archives': checks, 'source_files': len(payload), 'overleaf_files': len(overleaf),
                     'public_repo_files': len(public), 'all_zip_crc_passed': True}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT.parent / 'delivery_v4')
    args = parser.parse_args()
    main(args.output)
