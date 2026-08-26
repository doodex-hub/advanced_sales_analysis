# Migration Spec (Teknis) — advanced_sales_analysis

**Step:** 3 — Migration Spec
**Versi:** 18.0 → 19.0
**Ref:** `02_diff/02_DIFF_ANALYSIS.md`
**Tanggal:** 2026-08-26

> Dokumen ini memandu IMPLEMENTASI (step 6). Ini **bukan** dasar testing/acceptance criteria —
> itu datang dari `01b_BASELINE_SPEC.md` (step 1). Lihat step 5.

---

## 1. Ringkasan Strategi

Modul ini murni backend/compute (tidak ada view/XML, controller, asset, atau Owl — semua fase kondisional N/A, lihat `01a_MIGRATION_INTAKE.md` §2b). Diff analysis (Step 2) menemukan **satu** perubahan wajib: `sale.order.line.tax_id` di-rename `tax_ids` di core 19.0 (DIFF-01), dipakai modul di 2 baris. Semua hook lain (`_select_additional_fields()`, `_group_by_sale()`, `_get_invoice_lines()`) stabil 1:1 — strategi keseluruhan adalah **port langsung + satu rename wajib + bump versi manifest**, TIDAK ada rewrite struktural.

## 2. Strategi per File/Simbol

| File/simbol | Ref `DIFF-NNN` | Strategi migrasi | Risiko | Ref `BSL-NNN` |
|---|---|---|---|---|
| `advanced_sales_analysis/models/sale_report.py:114` — `line.tax_id.filtered(...)` | DIFF-01 | Rename `line.tax_id` → `line.tax_ids` | Rendah (rename mekanis, bukan perubahan logic — `.filtered()` tetap dipanggil di recordset yang sama, semantik pajak tidak berubah) | `[BSL-008]` |
| `advanced_sales_analysis/models/sale_report.py:118` — `line.tax_id.compute_all(...)` | DIFF-01 | Rename `line.tax_id` → `line.tax_ids` | Rendah, sama seperti di atas | `[BSL-008]` |
| `__manifest__.py` — `'version': '18.0.1.0.0'` | — (wajib standar, semua migrasi) | Bump ke `'19.0.1.0.0'` | Nihil | — |
| Semua field/method lain (`_select_additional_fields`, `_compute_amount_paid`, `_compute_amount_dp`, `_compute_waiting_for_payment_research`, `_compute_amount_received_research`) | DIFF-02, DIFF-03, DIFF-04, DIFF-06 | Port apa adanya, TIDAK ada perubahan kode | Nihil (dikonfirmasi stabil Step 2) | `[BSL-005]` s.d. `[BSL-011]` |

## 2b. Risk Analysis Terstruktur

### Critical Migration Blockers
*(Mencegah instalasi atau operasi inti di 19.0)*

| # | Isu | Lokasi | Rujukan knowledge base |
|---|---|---|---|
| 1 | Manifest version harus `19.0.x` | `__manifest__.py` | Standar migrasi, tidak spesifik ke `knowledge/` |
| 2 | `sale.order.line.tax_id` tidak ada lagi (rename `tax_ids`) — `AttributeError` saat compute/write kalau tidak di-fix | `models/sale_report.py:114,118` | `02_diff/02_DIFF_ANALYSIS.md` DIFF-01; kandidat baru `migration-tool/knowledge/version-diffs/18-to-19.md` (belum dipromosikan, lihat `migration-records/advanced_sales_analysis_18.0_19.0/SUMMARY.md` CAND-01) |

**Priority:** HIGH — kedua item wajib selesai sebelum G1 (install test) bisa lulus.

### OWL Widget yang Butuh Rewrite/Review
**N/A** — tidak ada Owl/JS custom (`01a_MIGRATION_INTAKE.md` §2b).

### Controller & Route
**N/A** — `controllers/controllers.py` kosong, tidak ada route aktif.

### Assets & Dependency
**N/A** — tidak ada `static/src/`, tidak ada key `assets` di manifest. Dependency (`base`/`sale`/`account`/`sale_management`) semua dikonfirmasi tersedia di 19.0 tanpa perubahan (Step 2).

### Kompatibilitas Data Model

| # | Isu | Lokasi | Priority | Ref `BSL-NNN` |
|---|---|---|---|---|
| 1 | `sale.order.line.tax_id`→`tax_ids` (rename, field `store=True`, kolom DB ikut berubah lewat mekanisme ORM core `sale` sendiri saat modul itu upgrade — bukan tanggung jawab migrasi modul ini menulis migration script data, cukup ikut ORM registry core) | `models/sale_report.py:114,118` | HIGH | `[BSL-008]` |

### Risiko Integrasi

| # | Isu | Lokasi | Priority |
|---|---|---|---|
| 1 | Kolisi `account.move.amount_paid` vs `account_payment` (`[BSL-006]`) — sudah ada sejak baseline 17.0/18.0, TIDAK bertambah parah di 19.0 (dikonfirmasi Step 2, DIFF-04). Bukan target perbaikan migrasi ini, tapi tetap dipantau di Step 8/9 kalau ada gejala baru. | `models/sale_report.py:24-41` | LOW (informasional, no action) |

### Urutan Prioritas Testing

1. Install & startup — manifest version, dependency (`base`/`sale`/`account`/`sale_management`), tidak ada error saat load registry.
2. Core compute flow — `_compute_asa_amount_to_invoice` HARUS jalan tanpa `AttributeError` (verifikasi langsung fix DIFF-01) untuk baris SO `state in ('sale','done')`.
3. `sale.report` pivot — 3 measure (`amount_received`, `waiting_for_payment`, `amount_to_invoice`) muncul dan terisi benar, granularitas GROUP BY tetap sama seperti baseline 18.0 (tidak ada gap baru seperti MF-01).
4. Regression suite existing (`tests/test_account_move.py`, `test_sale_order_line.py`, `test_sale_report.py`, `test_qa_browser.py`) — semua HARUS tetap lulus, adaptasi assertion HANYA kalau ada referensi field lama yang sudah di-rename di test itu sendiri (cek Step 6).

### View List (dulu Tree) Checklist
**N/A** — tidak ada view/XML sama sekali di modul ini.

### Estimasi Effort

| Area | Effort | Catatan |
|---|---|---|
| Rename `tax_id`→`tax_ids` (2 baris) + bump manifest | Sangat kecil (< 30 menit) | Perubahan mekanis, sudah teridentifikasi persis lokasinya |
| Regression test run (G1) | Kecil | 38 test existing (warisan migrasi 17→18), tinggal jalankan ulang di environment 19.0 |

## 3. Data Migration

**N/A untuk port kode saja** (`01a_MIGRATION_INTAKE.md` §3 — dikonfirmasi dev, tidak ada data produksi). Catatan teknis: rename kolom DB `tax_id`→`tax_ids` di `sale.order.line` ditangani otomatis oleh mekanisme upgrade ORM core modul `sale` sendiri (bagian dari upgrade Odoo 19.0 itu sendiri, bukan sesuatu yang modul custom ini perlu scripting tambahan) — relevan hanya kalau migrasi ini nanti jadi upgrade instance produksi (bukan scope project ini).

## 4. Scope

### Termasuk
- Rename `line.tax_id` → `line.tax_ids` di `models/sale_report.py` (2 lokasi).
- Bump `__manifest__.py` `version` ke `19.0.1.0.0`.
- Verifikasi semua hook/field lain TIDAK berubah (sudah dikonfirmasi Step 2, tidak ada aksi kode).
- Jalankan ulang test suite existing (38 test) di environment 19.0, adaptasi HANYA kalau ada test yang secara eksplisit merujuk `tax_id` di level Python test code.

### Di Luar Scope (sengaja, disetujui di intake)
- Memperbaiki bug/quirk lama yang dipertahankan dari baseline 18.0 (`[BSL-006]`, `[BSL-008]` dead-code path, `[BSL-013]` s.d. `[BSL-022]`) — bukan target migrasi ini, kecuali pemilik modul minta eksplisit.
- Perbaikan label field (`[BSL-017]`) — kosmetik, tidak install-blocking, tidak disentuh.
- Catatan non-kode `product_uom`→`product_uom_id` untuk dashboard eksternal (`02_DIFF_ANALYSIS.md` §1 catatan informasional) — di luar scope kode modul, diteruskan ke business/BI owner bukan dikerjakan AI.
