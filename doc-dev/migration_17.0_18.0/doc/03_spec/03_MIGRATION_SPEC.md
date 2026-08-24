# Migration Spec (Teknis) — advanced_sales_analysis

**Step:** 3 — Migration Spec
**Versi:** 17.0 → 18.0
**Ref:** `02_diff/02_DIFF_ANALYSIS.md`
**Tanggal:** 2026-08-21

> Dokumen ini memandu IMPLEMENTASI (step 6). Ini **bukan** dasar testing/acceptance criteria —
> itu datang dari `01_intake/01b_BASELINE_SPEC.md`. Lihat step 5.

---

## 1. Ringkasan Strategi

**Port langsung, tanpa rewrite kode.** Step 2 (`02_DIFF_ANALYSIS.md`) tidak menemukan satu pun breaking change pada API/hook yang dipakai modul ini — seluruh permukaan Python (`sale.report._select_additional_fields()`, `sale.order.line._compute_untaxed_amount_to_invoice()`/`_get_invoice_lines()`/`is_downpayment`, `account_payment.amount_paid`) byte-stable 17.0↔18.0. Modul tidak punya view/XML/JS/controller aktif, jadi seluruh kelas perubahan besar 17→18 (`<tree>`→`<list>`, chatter, kanban, Owl/JS) **tidak berlaku**.

Satu-satunya perubahan WAJIB: bump `version` di `__manifest__.py` dari `17.0.1.0.0` ke `18.0.1.0.0` (konvensi versi Odoo, prefix mayor harus cocok versi target — lihat Critical Migration Blocker #1 di bawah). Tidak ada perubahan business logic, field, atau struktur apa pun — konsisten `01a_MIGRATION_INTAKE.md` §5 (Scope Boundary: seluruh `BR/BSL` dan bug/quirk yang masih terbuka dipertahankan identik).

Satu item berstatus "kemungkinan aman, belum pasti" (DIFF-06, `@api.depends` melingkar) — tidak butuh perubahan kode, tapi WAJIB di-re-test eksekusi terhadap instance 18.0 sungguhan di Step 9 sebelum dianggap selesai (bukan diasumsikan dari analisis statis).

## 2. Strategi per File/Simbol

| File/simbol | Ref `DIFF-NNN` | Strategi migrasi | Risiko | Ref `BSL-NNN` |
|---|---|---|---|---|
| `__manifest__.py` (`version`) | — (Critical Migration Blocker #1 di bawah) | Ubah `'version': '17.0.1.0.0'` → `'18.0.1.0.0'`. Tidak ada perubahan lain di manifest (`depends`, `data` tetap sama — lihat `01a_MIGRATION_INTAKE.md` §2, keempat dependency dikonfirmasi ada di 18.0). | Tidak ada | — |
| `models/sale_report.py` — `SaleReport._select_additional_fields()` | DIFF-01 | **Copy 1:1, tidak ada perubahan.** Hook stabil. | Tidak ada | `[BSL-005]`, `[BSL-023]` |
| `models/sale_report.py` — `AccountMove.amount_paid`/`_compute_amount_paid`/`_compute_amount_dp` (8 field) | DIFF-02 | **Copy 1:1.** Kolisi dengan `account_payment` DIPERTAHANKAN apa adanya (bukan scope migrasi untuk diperbaiki). | Kolisi nama field carry-over (Tinggi, sudah ada di baseline, bukan risiko baru) | `[BSL-006]`, `[BSL-007]`, `[BSL-011]` |
| `models/sale_report.py` — `SaleOrderLine._compute_amount_to_invoice`/`_compute_waiting_for_payment_research`/`_compute_amount_received_research` (3 field) | DIFF-03, DIFF-04 | **Copy 1:1.** Dead-code `invoice_policy` (F-17) dan seluruh quirk lain DIPERTAHANKAN. | Bug carry-over (Tinggi untuk F-17, sudah ada di baseline) | `[BSL-008]`, `[BSL-009]`, `[BSL-010]`, `[BSL-021]` |
| `controllers/controllers.py`, `security/ir.model.access.csv`, `googleaeed8a7b9ec156e7.html` | — (tidak ada baris `DIFF-NNN` — bukan API native, murni file structural modul) | **Copy 1:1 apa adanya** (termasuk yang secara teknis "dead"/scaffold — F-07/F-12/F-14 bukan scope migrasi untuk dibersihkan, kecuali user putuskan lain). | Tidak ada risiko migrasi (tidak ada dampak runtime) | `[BSL-015]`, `[BSL-016]`, `[BSL-018]` |
| `static/description/` (`banner.png`, `icon.png`, `index.html`, `assets/*.png`) | — (bukan API native — aset marketing/listing Apps Store, tidak version-dependent) | **Copy 1:1.** Tidak ada perubahan format/konvensi Apps Store icon/banner antara 17.0→18.0 yang diketahui memengaruhi modul ini. | Tidak ada | — |
| `tests/*.py` (`common.py`, `test_sale_report.py`, `test_account_move.py`, `test_sale_order_line.py`, `test_qa_browser.py`) | — | **Copy 1:1** dari `source-codebase` sebagai starting point Step 9 — dijalankan ulang (bukan ditulis ulang) terhadap instance 18.0 untuk regression check. Kalau ada helper test yang memakai API test-framework Odoo yang berubah (`setUp`→`setUpClass`, dll — lihat `version-diffs/17-to-18.md` §1b), itu penyesuaian test infrastructure, dicek langsung saat Step 9 dijalankan, bukan bagian scope port kode modul. | Rendah — test infra Odoo (bukan kode modul), risiko diserap di Step 9 | — |

## 2b. Risk Analysis Terstruktur

### Critical Migration Blockers
*(Mencegah instalasi atau operasi inti di 18.0)*

| # | Isu | Lokasi | Rujukan knowledge base |
|---|---|---|---|
| 1 | Manifest `version` masih `17.0.1.0.0` — harus `18.0.x.x.x` agar konsisten konvensi Odoo (tidak strictly install-blocking, tapi WAJIB per konvensi & kejelasan versi target) | `__manifest__.py:18` | — (konvensi umum Odoo, tidak spesifik `version-diffs/17-to-18.md`) |

**Priority:** HIGH — perbaiki sebelum runtime testing apapun (trivial, satu baris).

**Tidak ada Critical Migration Blocker lain** — DIFF-01 s/d DIFF-05 (`02_DIFF_ANALYSIS.md` §1) semuanya "tidak berubah"/"tidak berlaku". Ini konsisten dengan `01a_MIGRATION_INTAKE.md` §2b: modul tidak punya view/JS/controller aktif, jadi seluruh kelas blocker umum 17→18 (`<tree>`→`<list>`, asset registration, `odoo.define`) tidak relevan.

### OWL Widget yang Butuh Rewrite/Review

**N/A** — modul tidak punya komponen Owl/JS (`01a_MIGRATION_INTAKE.md` §2b).

### Controller & Route

| # | Isu | Lokasi | Priority |
|---|---|---|---|
| 1 | `controllers/controllers.py` kosong (2 baris komentar) tetap di-import — TIDAK ada route aktif untuk dicek kompatibilitasnya. Copy apa adanya (`[BSL-016]`/F-12), bukan scope perbaikan. | `controllers/controllers.py`, `__init__.py` | Rendah — tidak ada risiko migrasi, murni carry-over scaffold |

### Assets & Dependency

| # | Isu | Lokasi | Priority |
|---|---|---|---|
| 1 | Tidak ada key `assets` di manifest (`[BSL-022]`/F-18) — TIDAK perlu ditambahkan untuk migrasi murni (modul tidak punya JS produksi). Kalau Step 9 memutuskan menambah Tour test baru di 18.0, key `assets` baru jadi relevan (keputusan testing, bukan migrasi kode) | `__manifest__.py` | Rendah — N/A untuk migrasi kode |
| 2 | 4 dependency (`base`, `sale`, `account`, `sale_management`) — semua dikonfirmasi ada & Community di 18.0 (`01a_MIGRATION_INTAKE.md` §2). Tidak ada perubahan `depends` diperlukan. | `__manifest__.py:depends` | — Tidak ada risiko |

### Kompatibilitas Data Model

| # | Isu | Lokasi | Priority | Ref `BSL-NNN` |
|---|---|---|---|---|
| 1 | `@api.depends` melingkar (`amount_to_invoice`/`waiting_for_payment`/`amount_received` di `sale.order.line`) — dikonfirmasi TIDAK bermasalah di eksekusi 17.0 (backfill), TAPI belum di-re-run terhadap 18.0 sungguhan. Tidak perlu perubahan kode untuk migrasi (bukan blocker terkonfirmasi), tapi WAJIB masuk test plan Step 5/9. | `models/sale_report.py:88-90` | Sedang (status verifikasi, bukan kode) | `[BSL-021]` |
| 2 | 11 field stored-compute (3 di `sale.order.line`, 8 di `account.move`) akan ikut ter-recompute massal saat instalasi/upgrade modul di database dengan data (relevan kalau nanti modul ini dipasang di instance 18.0 yang sudah punya data — di luar scope "port kode saja" project ini, tapi dicatat untuk kesadaran Step 6 G1/G2 kalau test dijalankan dengan demo data). | `models/sale_report.py` (semua field `store=True`) | Rendah (informasi, bukan aksi) | `[BSL-006]`, `[BSL-007]`, `[BSL-008]`, `[BSL-009]`, `[BSL-010]` |

### Risiko Integrasi

| # | Isu | Lokasi | Priority |
|---|---|---|---|
| 1 | Kolisi `amount_paid`/`_compute_amount_paid` dengan `account_payment` (auto-install bareng `account`) — carry-over 1:1 dari 17.0, TIDAK membaik/memburuk di 18.0 (DIFF-02). Bukan aksi migrasi, murni kesadaran risiko yang sudah ada di baseline. | `models/sale_report.py:22-41` | Tinggi (carry-over, bukan risiko baru) |
| 2 | Kalau environment testing 18.0 (Step 9/10) menginstall `point_of_sale`, hook `_select_additional_fields()` yang sama dipakai `_select_pos()` milik POS — perlu diperhatikan test UNION tetap sinkron (sudah terbukti sinkron di desain hook resmi, tapi belum pernah dites langsung dengan POS terinstall bersamaan di 17.0 maupun 18.0). | `models/sale_report.py:13-18` | Rendah — informasi untuk Step 9, bukan blocker |

### Urutan Prioritas Testing

1. Install & startup — manifest version bump, dependency (`base`/`sale`/`account`/`sale_management`) resolve bersih di 18.0.
2. Core computation flow — 3 field `sale.order.line` (`amount_received`, `waiting_for_payment`, `amount_to_invoice`) dan 8 field `account.move` menghasilkan nilai yang identik dengan 17.0 untuk skenario yang sama (regression terhadap `01b_BASELINE_SPEC.md`).
3. `sale.report` — Sales Analysis pivot terbuka normal, 3 measure baru muncul dan konsisten dengan nilai di `sale.order.line` (regression F-19 — UNION tidak boleh mismatch lagi di 18.0).
4. Persistensi data — field `store=True` ter-compute benar saat `create()`/`write()` invoice.
5. `@api.depends` melingkar (DIFF-06) — re-run test yang setara `test_ac_06_05_urutan_pembacaan_field_melingkar` terhadap 18.0.
6. Widget backend (Owl) — **N/A**, dilewati (tidak ada Owl/JS).

### View List (dulu Tree) Checklist

**N/A** — modul tidak punya view/XML sama sekali (`'data': []`).

### Estimasi Effort

| Area | Effort | Catatan |
|---|---|---|
| Bump manifest version | Trivial (1 baris) | — |
| Port kode Python (`models/sale_report.py`) | Trivial — copy tanpa modifikasi | Semua API stabil, dikonfirmasi Step 2 |
| Re-verifikasi `@api.depends` melingkar (DIFF-06) | Kecil — jalankan ulang test existing terhadap 18.0 | Bukan penulisan test baru, cukup re-run |
| Total | **Sangat rendah** — modul kecil, tidak ada view/JS/controller, semua dependency stabil | Konsisten kesimpulan Step 2: "tidak ditemukan breaking change yang memaksa perubahan kode" |

## 3. Data Migration

**N/A untuk project ini** — sifat migrasi `port kode saja` (`01a_MIGRATION_INTAKE.md` §3), tidak ada data produksi yang dipindah. Step 7 (`07_DATA_MIGRATION_PLAN.md`) tidak berlaku.

## 4. Scope

### Termasuk
- Copy `advanced_sales_analysis/` (seluruh isi: `models/`, `controllers/`, `security/`, `static/`, `__init__.py`) 1:1 dari `source-codebase` ke `target-codebase`.
- Bump `__manifest__.py` `version` → `18.0.1.0.0`.
- Re-run seluruh test existing (`tests/test_sale_report.py`, `tests/test_account_move.py`, `tests/test_sale_order_line.py`, `tests/test_qa_browser.py`) terhadap instance 18.0 (Step 9) — termasuk verifikasi eksplisit DIFF-06.

### Di Luar Scope (sengaja, disetujui di intake)
- Memperbaiki 15 finding terbuka (F-01 s/d F-18, minus F-06/F-08/F-19 yang sudah resolved) — dipertahankan identik sesuai `01a_MIGRATION_INTAKE.md` §5.
- Menambah key `assets`/Tour test baru — di luar scope port kode (F-18/`[BSL-022]` cuma dicatat sebagai limitasi, bukan item yang diminta diperbaiki).
- Membersihkan scaffold (`controllers/controllers.py` kosong, `security/ir.model.access.csv` menganggur, file Google verification) — dipertahankan apa adanya (F-07/F-12/F-14), bukan cleanup tugas migrasi.
