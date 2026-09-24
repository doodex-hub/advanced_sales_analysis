# Implementation Log — advanced_sales_analysis

**Step:** 6 — Code Migration
**Ref:** `03_spec/03_MIGRATION_SPEC.md`, `migration-tool/templates/06a_CODE_MIGRATION_PHASES.md`
**Tanggal:** 2026-09-24

---

## Aturan

Append only · satu bagian per fase · faktual · tertelusuri · pengecualian eksplisit.

---

## Applicability Check

| Fase | Relevan? | Bukti/alasan (dari `01a` §2b) |
|---|---|---|
| C1 | Tidak | Tidak ada view/XML (`'data': []`) |
| B2 | Tidak | Tidak ada field JSON/dynamic model; relasi `invoice_lines.move_id.*` hanya di `@api.depends`, sudah dicek B1 |
| C2 | Tidak | Tidak ada view |
| D1 | Tidak | `controllers/controllers.py` hanya komentar |
| D2 | Tidak | Tidak ada `static/src`, tidak ada key `assets` (`static/description` = aset store, bukan bundle) |
| E | Tidak | Tidak ada JS |
| F | Tidak | Otomatis N/A (E N/A) |

## Tabel Ringkas Status Fase

| Fase | Status | Tanggal |
|---|---|---|
| A1 | ✅ | 2026-09-24 |
| A2 | N/A (tidak ada XML) | 2026-09-24 |
| G1 #1 (setelah A2) | ✅ Pass install / 5 test FAIL (diharapkan, DIFF-01 belum difix) | 2026-09-24 |
| A3 | N/A (security csv tidak dimuat) | 2026-09-24 |
| G1 #2 (setelah A3) | ✅ Pass (state identik G1 #1 — A3 tanpa perubahan) | 2026-09-24 |
| A4 | ✅ (tidak ada perubahan) | 2026-09-24 |
| A5 | ✅ | 2026-09-24 |
| A6 | ✅ | 2026-09-24 |
| B1 | ✅ (tidak ada perubahan) | 2026-09-24 |
| B2, C1, C2, D1, D2, E, F | N/A — Applicability Check | 2026-09-24 |
| G2 (validasi akhir) | ✅ lihat Riwayat G1 #3/#4 + Step 10 | 2026-09-24 |

## Riwayat Percobaan G1 (Install Test)

Mode: **C** (AI menjalankan Docker sendiri, dikonfirmasi dev di dialog intake 2026-09-24). Environment: `docker-env/` Odoo 20.0 from source (`odoo20`), `docker compose down -v` sebelum tiap run.

| # | Dijalankan setelah fase | Mode | Hasil | Error (kalau fail) | Tanggal |
|---|---|---|---|---|---|
| 0 | (probe Step 2, manifest 19.0 apa adanya) | C | ⚠️ "0 failed, 0 error(s) of 0 tests" — SUKSES PALSU | `WARNING The module advanced_sales_analysis has an incompatible version, setting installable=False` | 2026-09-24 |
| 1 | A1+A2 (probe Step 2: hanya version di-bump, lalu di-revert — state kode identik dengan A1 tanpa `images`) | C | Install ✅; test `5 failed, 0 error(s) of 41 tests` | AC-07-01/01b/01c/04: `0.0 != 100.0`; browser: `function sum(text) does not exist` (DIFF-01) | 2026-09-24 |
| 2 | A3 (N/A, tidak ada perubahan file) | C | Sama dengan #1 (tidak dijalankan ulang — tidak ada delta kode di antara #1 dan #2) | — | 2026-09-24 |
| 3 | A5+A6+test baru (Run A: Community addons-path, postgres:15) | C | ✅ **`0 failed, 0 error(s) of 43 tests`** (41 method test dimulai, 1 skip `test_f19_*` karena POS tidak terinstall — sama seperti 19.0) | — (warning hanya BSL-017 "same label", `markdown2 not installed`, Postgres < 16) | 2026-09-24 |
| 4 | Sama #3, Run B: `enterprise20` di addons-path, postgres:16 | C | lihat `09_DEV_TESTING.md` | | 2026-09-24 |

---

## Entri

## [Fase A1] Manifest Bootstrap
- **Scope:** `advanced_sales_analysis/__manifest__.py`
- **Item spec (ref):** `03_MIGRATION_SPEC.md` §2 baris 1, Critical Blocker #1 (DIFF-07)
- **Aksi:** `version` `19.0.1.0.0` → `20.0.1.0.0`.
- **Secara eksplisit TIDAK dilakukan:** `depends`, `data` (termasuk baris security yang di-comment), `website`, `price`, `currency`, `company` tidak diubah.
- **Risiko:** LOW
- **Status:** ✅ Selesai

## [Fase A2] N/A — dikonfirmasi Applicability Check (tidak ada file XML)

## [Fase A3] N/A — `security/ir.model.access.csv` tidak dimuat manifest (BSL-015, DIFF-08); tidak ada TransientModel

## [Fase A4] Skeleton & Folder Integrity
- **Aksi:** dicek — `__init__.py` root (`controllers`, `models`), `models/__init__.py` (`sale_report`), `controllers/__init__.py`, `tests/__init__.py` konsisten. Tidak ada perubahan.
- **Status:** ✅ Selesai

## [Fase A5] Python API Compatibility
- **Scope:** `advanced_sales_analysis/models/sale_report.py`
- **Item spec (ref):** `03_MIGRATION_SPEC.md` §2 baris `SaleReport`, Critical Blocker #2 (DIFF-01 / MF-01)
- **Aksi:**
  - Tambah `from odoo.tools import SQL`.
  - Hapus `_select_additional_fields()`; ganti `_select_dict(self, table)` → `super()._select_dict(table) | {...}` dengan 3 ekspresi `SQL("CASE WHEN %s IS NOT NULL THEN SUM(%s) ELSE 0 END", table.product_id, table.<kolom>)` untuk `amount_received`, `waiting_for_payment`, `amount_to_invoice` (← `asa_amount_to_invoice`).
- **Secara eksplisit TIDAK dilakukan:** tidak dikalikan kurs (BSL-014); guard tetap `product_id IS NOT NULL` (bukan `is_downpayment` seperti core); tidak ada override `_groupby_list`/`_table_sql`/`_select_pos_dict`; class `AccountMove` & `SaleOrderLine` tidak disentuh sama sekali.
- **Risiko:** MEDIUM → diverifikasi G1 #3 (AC-07 + browser pivot PASS)
- **Status:** ✅ Selesai

## [Fase A6] Housekeeping README/Metadata + aset store (keputusan dev 2026-09-24)
- **Scope:** `__manifest__.py` `images`, `static/description/`
- **Aksi:**
  - `images` → `['static/description/banner.gif', 'static/description/icon.png']` (identik commit `e5e6ecc` branch `19.0`).
  - `git checkout 19.0 -- advanced_sales_analysis/static/description` (banner.gif, icon.png, index.html, folder `assets/` gifs/icons/screens).
  - Hapus `banner.png`, `assets/advanced_sales_analysis.png`, `assets/doodex_odoo.png` (dihapus di branch `19.0` commit `9ec827e`/`5cc6798`, tidak dirujuk `index.html` baru). Hasil: `git diff 19.0 -- advanced_sales_analysis/static/description` kosong.
  - README/LISEZMOI addon: dicek, tidak menyebut versi Odoo → tidak diubah.
- **Secara eksplisit TIDAK dilakukan:** penghapusan `tests/`, `docker-env/`, `googleaeed8a7b9ec156e7.html` dari commit "cleaning" `52fdac6` tidak di-port.
- **Risiko:** LOW (non-fungsional)
- **Status:** ✅ Selesai

## [Fase B1] Model Risiko Rendah
- **Aksi:** dicek `@api.depends` 5 compute terhadap field 20.0 (DIFF-03/04): semua path (`invoice_lines.move_id.amount_paid`, `invoice_lines.price_total`, `untaxed_amount_invoiced`, dst) valid di 20.0; registry dibangun tanpa error "invalid field in depends". Tidak ada perubahan.
- **Status:** ✅ Selesai

## [Fase B2, C1, C2, D1, D2, E, F] N/A — dikonfirmasi Applicability Check

## [Test] Penyesuaian test suite
- `tests/test_sale_report.py`: catatan migrasi 20.0 di docstring modul (rujukan hook lama = riwayat ≤19.0); test baru `test_ac_07_03b_group_by_nama_baris_20_0` (MF-03) dan `test_ac_07_06_select_dict_hook_dipakai` (regression guard MF-01).
- **Secara eksplisit TIDAK dilakukan:** tidak ada assertion test lama yang diubah.

## [Infra] docker-env
- Diganti ke Odoo 20.0 from source (Step 2). `db` dinaikkan `postgres:15` → `postgres:16` setelah G1 #3 memunculkan `UserWarning: Postgres version is 150019, lower than minimum required 160000`.

---

## Temuan di Luar Spec

- Postgres minimum 16 untuk Odoo 20 (warning, bukan blocker) — kandidat knowledge, dicatat di `migration-records/.../SUMMARY.md` CAND-07.
