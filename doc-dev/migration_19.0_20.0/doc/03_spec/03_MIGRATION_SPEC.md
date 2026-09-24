# Migration Spec (Teknis) — advanced_sales_analysis

**Step:** 3 — Migration Spec
**Versi:** 19.0 → 20.0
**Ref:** `02_diff/02_DIFF_ANALYSIS.md`, `01_intake/01a_MIGRATION_INTAKE.md` §5
**Tanggal:** 2026-09-24
**Status:** ✅ Selesai

---

## 1. Ringkasan Strategi

Port langsung. Hanya dua perubahan kode wajib: (1) bump versi manifest (DIFF-07), (2) tulis ulang hook `sale.report` dari `_select_additional_fields()` (string SQL) ke `_select_dict(table)` (objek `SQL`) dengan ekspresi setara 1:1 (DIFF-01). Semua compute `account.move`/`sale.order.line` tidak disentuh (DIFF-03/04/05 stabil, 36 test PASS di probe). Ditambah perubahan non-fungsional yang disetujui dev: aset store dari branch rilis `19.0`. Test disesuaikan hanya kalau perilaku CORE 20.0 berubah (DIFF-06) — test yang assert perilaku modul tidak diubah assertion-nya.

## 2. Strategi per File/Simbol

| File/simbol | Ref DIFF | Strategi migrasi | Risiko | Ref BSL |
|---|---|---|---|---|
| `__manifest__.py` `version` | DIFF-07 | `19.0.1.0.0` → `20.0.1.0.0` | Rendah | — |
| `__manifest__.py` `images` | DIFF-09 | `['static/description/banner.png']` → `['static/description/banner.gif', 'static/description/icon.png']` (salin persis dari commit `e5e6ecc` branch `19.0`) | Rendah (non-fungsional) | — |
| `static/description/*` | — (keputusan dev) | Ambil dari branch `19.0`: `banner.gif`, `icon.png`, `index.html`, folder `assets/`; hapus `banner.png` (branch `19.0` menghapusnya). Pakai `git checkout 19.0 -- advanced_sales_analysis/static/description` + `git rm banner.png`. Tidak menyentuh `tests/`, `docker-env/`, `googleaeed8a7b9ec156e7.html` (BSL-018 dipertahankan). | Rendah | — |
| `models/sale_report.py` `SaleReport._select_additional_fields()` | DIFF-01 | Ganti dengan `_select_dict(self, table)`: `return super()._select_dict(table) \| {...}` dengan 3 key: `amount_received` → `SQL("CASE WHEN %s IS NOT NULL THEN SUM(%s) ELSE 0 END", table.product_id, table.amount_received)`; `waiting_for_payment` → idem `table.waiting_for_payment`; `amount_to_invoice` → idem `table.asa_amount_to_invoice`. Import `from odoo.tools import SQL`. **Tidak** dikalikan `rate` (BSL-014 dipertahankan). Guard `product_id IS NOT NULL` dipertahankan meski core 20.0 memakai `is_downpayment` untuk kolomnya sendiri — kita menyalin semantik modul, bukan core. `table.product_id` sudah ada di `_groupby_list` core, jadi `CASE` di luar agregat valid. | Sedang → mitigasi test AC-07 + browser pivot | BSL-005, BSL-014, BSL-023 |
| `models/sale_report.py` `AccountMove`, `SaleOrderLine` (semua compute) | DIFF-03/04/05 | Tidak diubah | Tidak ada | BSL-006…BSL-011, BSL-024 |
| `security/ir.model.access.csv` | DIFF-08 | Tidak diubah (tidak dimuat) | Tidak ada | BSL-015 |
| `controllers/` | — | Tidak diubah | Tidak ada | BSL-016 |
| `tests/test_sale_report.py` | DIFF-01, DIFF-02, DIFF-06 | (a) Docstring yang menyebut `_select_additional_fields()`/`_select_pos()` diperbarui ke `_select_dict()`/`_select_pos_dict()` (assertion tidak berubah). (b) `test_ac_07_03_group_by_granularitas_18_0` — tetap (harga beda → 2 baris, lulus di probe); tambah test baru `test_ac_07_03b_group_by_nama_baris_20_0` merekam MF-03 (deskripsi beda → 2 baris). (c) Tambah test `test_ac_07_06_select_dict_hook_dipakai` — memastikan 3 key ada di `_select_dict()` dan TIDAK ada method `_select_additional_fields` di `sale.report` (regression guard DIFF-01). (d) `test_f19_union_kompatibel_dengan_point_of_sale` — docstring diperbarui; tetap skip kalau POS tidak terinstall (AC-07-05 tetap terbuka). | Rendah | BSL-023 |
| `tests/test_qa_browser.py` | DIFF-10 | Tidak diubah (selector stabil) | Rendah | BSL-001 |
| `docker-env/*` | — | Sudah diganti di Step 2 (Odoo 20 from source) | Rendah | — |

## 2b. Risk Analysis Terstruktur

### Critical Migration Blockers

| # | Isu | Lokasi | Rujukan |
|---|---|---|---|
| 1 | Manifest version harus `20.0.x` (tanpa itu: `installable=False`, "0 tests" sukses palsu) | `__manifest__.py` | DIFF-07, probe 1 |
| 2 | `_select_additional_fields` tidak dipanggil di 20.0 → measure 0/NULL, pivot crash `sum(text)` | `models/sale_report.py:13-18` | DIFF-01, probe 2; kandidat knowledge `migration-records/.../SUMMARY.md` CAND-01 |

**Priority:** HIGH — keduanya di Fase A.

### OWL Widget — N/A (tidak ada JS).
### Controller & Route — N/A (controller kosong).
### Assets & Dependency — tidak ada perubahan `depends`; aset store = file statis `static/description` (bukan bundle asset).

### Kompatibilitas Data Model

| # | Isu | Lokasi | Priority | Ref BSL |
|---|---|---|---|---|
| 1 | Kolom SQL view `sale.report` dibangun ulang dari `_select_dict` — nama & tipe field tidak berubah (`Float`) | `sale_report.py` | Tinggi | BSL-005 |

### Risiko Integrasi

| # | Isu | Lokasi | Priority |
|---|---|---|---|
| 1 | `pos_sale` terinstall → `amount_to_invoice` baris POS terisi (MF-02, diterima) | `pos_sale/report/sale_report.py:57` | Rendah |
| 2 | Modul lain yang meng-override `_select_dict` (mis. `sale_margin`, `sale_stock`, `partner_commission` Enterprise) — pola `super() \| {...}` komposabel, tidak ada kunci yang sama | — | Rendah |
| 3 | Enterprise di addons-path (`web_enterprise` auto-install) — tidak mengubah `sale.report` | — | Rendah → diverifikasi run Enterprise di Step 9 |

### Urutan Prioritas Testing
1. Install & startup (manifest, registry, tanpa error/warning baru selain BSL-017).
2. `sale.report` nilai 3 kolom (AC-07) + pivot browser (AC-01-02).
3. Compute `sale.order.line`/`account.move` (AC-02…AC-06) — regresi.
4. Run Enterprise-like addons-path.

### View List (dulu Tree) Checklist — N/A (tidak ada view).

## 3. Data Migration

N/A — port kode saja (intake §3). Kolom `sale.report` adalah view (dibangun ulang tiap install/upgrade); field stored lain tidak berubah struktur.

## 4. Scope

### Termasuk
- Bump manifest, port `_select_dict`, aset store, penyesuaian docstring/test untuk perubahan core, test regresi baru DIFF-01 & MF-03.

### Di Luar Scope (sengaja, disetujui di intake)
- Semua quirk BSL-011…BSL-021 (tidak diperbaiki).
- Override khusus untuk baris POS (MF-02 — diterima apa adanya).
- Penghapusan `tests/`/`docker-env/` ala commit "cleaning" branch `19.0`.

## 5. Keputusan desain yang diambil AI (dicatat sesuai "Eksekusi Berkelanjutan")

- **Guard `product_id IS NOT NULL` vs `is_downpayment`:** core 20.0 mengganti guard kolomnya sendiri ke `is_downpayment IS NOT TRUE`. Modul TETAP memakai `product_id IS NOT NULL` — menyalin semantik 19.0 modul (BSL-005). Alternatif (ikut core) akan mengubah nilai baris down payment (baris DP punya `product_id`, jadi guard lama menghitungnya; guard core tidak) → perubahan business logic, dilarang.
- **Tanpa `rate`:** BSL-014 (tidak dikonversi mata uang) dipertahankan.
