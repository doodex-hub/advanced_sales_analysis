# Code Review — advanced_sales_analysis

**Step:** 8 — Code Review (gate)
**Ref:** `03_spec/03_MIGRATION_SPEC.md`, `05_acceptance/05a_MIGRATION_ACCEPTANCE_CRITERIA.md`, `06_implementation/06c_IMPLEMENTATION_LOG.md`, `01_intake/01b_BASELINE_SPEC.md`
**Odoo Version:** 19.0
**Files reviewed:** `advanced_sales_analysis/__manifest__.py`, `advanced_sales_analysis/models/sale_report.py` (seluruh isi, tidak hanya diff), `advanced_sales_analysis/tests/test_sale_order_line.py` (method baru + konteks sekitarnya)
**Tanggal:** 2026-08-26

---

## A. Issues (Lint, Konvensi Odoo, Business Logic, Security, Performance, Code Quality)

| ID | Severity | Kategori | File | Baris | Issue | Rekomendasi |
|---|---|---|---|---|---|---|
| CR-01 | 🔵 Info | Code Quality | `models/sale_report.py` | 90 | `asa_amount_to_invoice` masih ber-`string='Amount Received'` (label salah, warisan `[BSL-017]` sebelum rename MF-02) — TIDAK diperbaiki saat rename `tax_id`→`tax_ids` (di luar scope A5, murni label kosmetik) | Tidak ada aksi — di luar scope migrasi ini (`03_MIGRATION_SPEC.md` §4 "Di Luar Scope"), dicatat di sini murni supaya reviewer sadar, bukan kelewatan |
| CR-02 | 🔵 Info | Code Quality | `tests/test_sale_order_line.py` | (test baru) | Test `test_ac_06_03b_tax_ids_rename_price_include` membuat `product.product`+`account.tax` baru langsung di dalam method (bukan di `common.py::setUpClass`) — konsisten pola "self-contained, tidak menyentuh fixture bersama" yang disebutkan di `06c_IMPLEMENTATION_LOG.md`, tapi berarti fixture ini tidak reusable test lain | Tidak ada aksi wajib — trade-off yang disengaja (isolasi lebih penting dari reuse untuk 1 test), boleh direfactor ke `common.py` di masa depan kalau ada test lain yang butuh tax price-included |

Tidak ada temuan 🔴 Critical maupun 🟡 Warning — perubahan kode migrasi ini (bump manifest + rename 2 baris) genuinely minimal dan tidak membuka celah baru di kategori Konvensi Odoo/Business Logic/Security/Performance. Modul warisan (`[BSL-006]`, `[BSL-008]` dead-code, `[BSL-013]` string literal, dst) TIDAK direview ulang di sini sebagai temuan baru — semua sudah tercatat sebagai baseline yang dipertahankan di `01b_BASELINE_SPEC.md`, bukan celah migrasi ini.

**Severity:** 🔴 Critical (bug/security/AC tidak cover — wajib fix) · 🟡 Warning (convention/performance — fix kalau memungkinkan) · 🔵 Info (saran, opsional)

## B. Gap Analysis — Implementasi vs Migration Spec

| Spec item (`DIFF-NNN`/Fase) | Implementasi | Status | Catatan |
|---|---|---|---|
| Critical Blocker #1 — bump manifest `19.0.1.0.0` | `__manifest__.py:18` | ✅ Sesuai | — |
| Critical Blocker #2 / DIFF-01 — rename `tax_id`→`tax_ids` | `models/sale_report.py:114,118` | ✅ Sesuai | Diverifikasi G1 (39/39 test pass, termasuk AC-06-03b yang secara spesifik melewati baris ini) |
| Fase B1 — review kelengkapan `@api.depends` | Direview manual (`06c_IMPLEMENTATION_LOG.md` [Fase B1]) | ✅ Sesuai | Tidak ada field yang direferensikan hilang/berubah nama di 19.0 selain `tax_id` (sudah ditangani) |
| Fase A2/A3/B2/C1/C2/D1/D2/E/F | N/A (Applicability Check) | ✅ Sesuai — tidak ada implementasi yang seharusnya ada tapi terlewat | Dikonfirmasi ulang: tidak ada file XML/JS/controller/asset baru yang diam-diam ditambahkan/dilewatkan |

## C. Gap Analysis — Implementasi vs Acceptance Criteria

| AC ID | Behavior | Status | Catatan |
|---|---|---|---|
| AC-01 s.d. AC-05 | Instalasi, kolisi `amount_paid`, komponen DP, `amount_received`, `waiting_for_payment` | ✅ Diverifikasi G1 (bagian dari 39 test) | Tidak ada kode yang menyentuh area ini — port apa adanya, lulus test warisan |
| AC-06-01 s.d. AC-06-04 | `asa_amount_to_invoice` (termasuk dead-code path F-17, urutan `@api.depends`) | ✅ Diverifikasi G1 | Behavior identik 18.0 — dikonfirmasi lewat test warisan, TIDAK ada regresi dari rename A5 |
| **AC-06-03b** (BARU) | Fix DIFF-01 lewat jalur `price_include`/`compute_all()` | ✅ Diverifikasi G1 — test lulus, hasil numerik `100.0` sesuai ekspektasi | Ini AC yang paling kritis untuk gate ini — tanpa AC ini, jalur `tax_ids.compute_all()` (baris 118) tidak akan pernah teruji karena tidak ada test lain yang memasang pajak price-included |
| AC-07-01 s.d. AC-07-04 | `sale.report` SQL view | ✅ Diverifikasi G1 | Granularitas GROUP BY dikonfirmasi stabil (DIFF-02), tidak ada perubahan kode |
| AC-07-05 | UNION dengan POS terinstall | ⚠️ **Belum diverifikasi eksekusi** (gap warisan, dicatat eksplisit sejak `05a`) | Tetap gap testing terbuka — TIDAK memblokir gate Step 8 (sudah didokumentasikan sebagai gap yang diketahui & disetujui, bukan celah baru), tapi harus tetap disebut ke Step 9/10 (lihat `09_DEV_TESTING.md`) |

## D. Cek Khusus Migrasi — P1 Fidelity

- [x] Tidak ada perubahan behavior yang tidak disengaja — satu-satunya perubahan kode (rename `tax_id`→`tax_ids`) adalah rename accessor mekanis wajib kompatibilitas, TIDAK mengubah semantik pajak/hasil numerik apa pun (dikonfirmasi G1: hasil `_compute_asa_amount_to_invoice` untuk skenario tanpa pajak IDENTIK dengan sebelumnya; skenario BARU dengan pajak price-included, `AC-06-03b`, menghasilkan angka yang benar sesuai formula pajak standar Odoo, bukan angka yang "berubah karena migrasi").
- [ ] Ada — daftar & keputusan: *(kosong, tidak berlaku)*

**Cek tabrakan nama method dengan Odoo core (DUA ARAH):**

1. **Arah 1** (modul menimpa method core dengan nama sama, kehilangan side-effect core diam-diam): Method yang di-override modul ini ke model core: `_select_additional_fields()` (satu-satunya override method core sungguhan, lewat `super()` dengan benar — dikonfirmasi `models/sale_report.py:14`). Method compute lain (`_compute_amount_paid`, `_compute_amount_dp`, `_compute_waiting_for_payment_research`, `_compute_amount_received_research`, `_compute_asa_amount_to_invoice`) BUKAN override method core — nama-nama ini tidak match method resmi apa pun di `native-target` (dikonfirmasi Step 2, grep repo-wide). **Kolisi METHOD (bukan cuma field) yang genuinely ada:** `_compute_amount_paid` — modul ini DAN `account_payment` (core) SAMA-SAMA mendefinisikan method dengan nama persis ini di `account.move` (masing-masing sebagai compute callback field mereka sendiri, `amount_paid` Float vs `amount_paid` Monetary). Ini `[BSL-006]`, kolisi LAMA (sejak baseline 17.0/18.0, byte-identik di 19.0 per DIFF-04) — bukan temuan baru migrasi 18→19, sudah didokumentasikan lengkap dengan keputusan "dipertahankan apa adanya" di `01b_BASELINE_SPEC.md`.
2. **Arah 2** (core 19.0 menambah field/method BARU bernama sama seperti yang modul definisikan): Sudah dicek tuntas di Step 2 (`02_DIFF_ANALYSIS.md` DIFF-04) — grep repo-wide `enterprise19.0/odoo/addons` (Community+Enterprise) untuk SEMUA nama field/method yang modul definisikan (`amount_received`, `waiting_for_payment`, `asa_amount_to_invoice`, `amount_paid`, `amount_paid_cn`, `amount_dp*`, `amount_refund*`) — **tidak ada kolisi baru**. `sale.order.line.amount_to_invoice` (field core yang MEMICU rename MF-02 di migrasi 17→18) TETAP ada tidak berubah di 19.0, TIDAK collide lagi karena modul sudah pakai nama `asa_amount_to_invoice` sejak baseline 18.0.

- [x] Sudah dicek (kedua arah) — tidak ada tabrakan BARU dengan core/Enterprise. Satu kolisi METHOD lama (`[BSL-006]`) tetap ada, sudah didokumentasikan sebagai baseline yang dipertahankan, bukan gap migrasi 18→19 yang butuh keputusan baru.
- [ ] Ada tabrakan ditemukan (baru): *(kosong, tidak berlaku)*

## E. Perubahan Tak Tertelusuri (di luar spec)

- [x] Tidak ada perubahan yang tidak tertelusuri ke spec — seluruh diff kode (`git diff` antara `source-codebase` dan `target-codebase` saat ini) hanya menyentuh 3 baris (`__manifest__.py` version, `sale_report.py` 2 baris rename) + 1 test method baru, semuanya tertelusuri ke `03_MIGRATION_SPEC.md` §2/§2b dan `05a_MIGRATION_ACCEPTANCE_CRITERIA.md` AC-06-03b.

## F. Kontribusi ke Knowledge Base

- [x] Tidak ada temuan baru yang perlu dicatat — temuan DIFF-01/CAND-01 sudah dicatat sejak Step 2 di `migration-records/advanced_sales_analysis_18.0_19.0/SUMMARY.md`. Tidak ada temuan tambahan dari review kode ini yang belum tercatat di sana.

## G. Verdict

- Ringkasan Issues: 0 🔴 · 0 🟡 · 2 🔵
- [x] ✅ **Lulus** — tidak ada 🔴, lanjut ke step 9
- [ ] ❌ Ditolak

**Issue 🔴 yang wajib difix sebelum lanjut:** Tidak ada.
