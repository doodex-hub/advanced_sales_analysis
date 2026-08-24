# Code Review — advanced_sales_analysis

**Step:** 8 — Code Review (gate)
**Ref:** `03_spec/03_MIGRATION_SPEC.md`, `05_acceptance/05a_MIGRATION_ACCEPTANCE_CRITERIA.md`, `06_implementation/06c_IMPLEMENTATION_LOG.md`, `01_intake/01b_BASELINE_SPEC.md`
**Odoo Version:** 18.0
**Files reviewed:** `advanced_sales_analysis/__manifest__.py`, `advanced_sales_analysis/models/sale_report.py`, `advanced_sales_analysis/controllers/controllers.py`, `advanced_sales_analysis/security/ir.model.access.csv`, `advanced_sales_analysis/tests/*.py`
**Tanggal:** 2026-08-21

---

## A. Issues (Lint, Konvensi Odoo, Business Logic, Security, Performance, Code Quality)

| ID | Severity | Kategori | File | Baris | Issue | Rekomendasi |
|---|---|---|---|---|---|---|
| CR-01 | 🔴 Critical | Business Logic / Konvensi Odoo | `models/sale_report.py` | 88-90 (`amount_to_invoice = fields.Float(..., compute='_compute_amount_to_invoice', ...)`) | **BARU DITEMUKAN saat cek tabrakan nama method dengan core (WAJIB Step 8) — belum tercatat di Step 2/6.** Core `sale` 18.0 menambahkan field BARU `sale.order.line.amount_to_invoice` (`Monetary`, `compute='_compute_amount_to_invoice'`, `compute_sudo=True`, `addons/sale/models/sale_order_line.py:294-298`) — field ini **TIDAK ADA di 17.0** (17.0 hanya punya `untaxed_amount_to_invoice`). Modul ini mendefinisikan field DAN method compute dengan **nama PERSIS SAMA** pada model yang SAMA. Karena `advanced_sales_analysis` depends langsung ke `sale` (load belakangan di registry), definisi modul MENIMPA TOTAL definisi+compute core (dikonfirmasi log instalasi: "Prepare computation of sale.order.line.amount_to_invoice" cuma sekali, tidak ada warning tipe field beda, method core TIDAK PERNAH terpanggil). **Efek berantai:** `sale.order.amount_to_invoice` (field baru core lain, `@api.depends('order_line.amount_to_invoice')`, `addons/sale/models/sale_order.py:239,754-757`) ikut memakai nilai yang salah (semantik modul, bukan semantik core "Un-invoiced Balance" tax-inclusive) → dipakai `account_move.py` core (`_get_partner_credit_warning_exclude_amount`, `_compute_partner_credit`, `addons/sale/models/account_move.py:165-200`) untuk **kalkulasi credit limit/warning kredit partner** → angka credit limit warning jadi salah kalau fitur ini aktif di database target. Juga dipakai `res_partner.py:100` untuk stat aggregate "amount to invoice" di form partner. **Ini BUKAN bug lama yang diwarisi (`[DIWARISI-SOURCE]`)** — collision ini genuinely baru muncul karena field core 18.0 ini tidak ada di 17.0, jadi TIDAK bisa "dipertahankan identik" (di 17.0 tidak ada apa pun untuk collide). Dicatat lengkap di `FINDINGS.md` MF-02. | **BLOCKING — lihat `FINDINGS.md` MF-02 untuk 3 opsi + rekomendasi. Perlu keputusan user, bukan diputuskan sepihak (menyentuh fitur financial core: credit limit).** |
| CR-02 | 🔵 Info | Code Quality | `advanced_sales_analysis/__manifest__.py` | 22-24 | `security/ir.model.access.csv` tetap ada secara fisik & di-comment (F-07/`[BSL-015]`, dipertahankan sesuai baseline) — bukan issue baru, dicatat di sini cuma untuk kelengkapan cross-reference, tidak butuh aksi Step 8. | Tidak ada — sudah diputuskan dipertahankan di Step 1 intake. |
| CR-03 | 🔵 Info | Code Quality | `controllers/controllers.py` | 1-2 | File kosong tetap di-import (F-12/`[BSL-016]`, dipertahankan sesuai baseline). | Tidak ada — sudah diputuskan dipertahankan di Step 1 intake. |

**Severity:** 🔴 Critical (bug/security/AC tidak cover — wajib fix) · 🟡 Warning (convention/performance — fix kalau memungkinkan) · 🔵 Info (saran, opsional)

> **CR-02/CR-03 bukan "Issue" dalam arti perlu fix** — keduanya adalah bug/quirk 17.0 yang SUDAH diputuskan dipertahankan (bukan diperbaiki) di `01a_MIGRATION_INTAKE.md`. Ditulis di tabel ini murni untuk kelengkapan audit trail Step 8 (semua deviasi dari "kode bersih ideal" tercatat di satu tempat), bukan untuk dieksekusi.

## B. Gap Analysis — Implementasi vs Migration Spec

| Spec item (`DIFF-NNN`/Fase) | Implementasi | Status | Catatan |
|---|---|---|---|
| DIFF-01 s/d DIFF-05 | Semua sesuai `03_MIGRATION_SPEC.md` — port 1:1, cuma bump manifest version | ✅ Match | — |
| Critical Migration Blocker #1 (manifest version) | `__manifest__.py:18` → `18.0.1.0.0` | ✅ Match | Fase A1, `06c_IMPLEMENTATION_LOG.md` |
| MF-01 (granularitas `sale.report`, ditemukan Step 6) | Test disesuaikan ke baseline 18.0 sesuai keputusan user (Opsi 1) | ✅ Match (setelah keputusan) | Tidak ada di `03_MIGRATION_SPEC.md` awal karena ditemukan belakangan — spec TIDAK diupdate ulang untuk ini (bukan strategi implementasi, cuma acceptance criteria) |
| **CR-01/MF-02 (kolisi `amount_to_invoice` dengan core)** | **Tidak ada di `03_MIGRATION_SPEC.md`/`02_DIFF_ANALYSIS.md` — GAP di analisis Step 2/3, baru ketahuan Step 8** | ❌ **Gap** | Step 2 DIFF-03 mengecek `_compute_untaxed_amount_to_invoice()` (method LAMA yang tetap ada) tapi tidak mengecek apakah core menambah field/method BARU dengan nama yang sama seperti field modul sendiri. Lihat §F untuk kandidat perbaikan checklist Step 2. |

## C. Gap Analysis — Implementasi vs Acceptance Criteria

| AC ID | Behavior | Status | Catatan |
|---|---|---|---|
| AC-01 s/d AC-07 (minus AC-07-03) | Semua ter-cover implementasi (copy 1:1), diverifikasi eksekusi Step 6 (38 test, 0 failed) | ✅ Match | — |
| AC-07-03 | Diperbarui sesuai MF-01, diverifikasi eksekusi | ✅ Match (setelah update) | — |
| **(baru) AC terkait `amount_to_invoice` vs core credit limit** | **Belum ada AC yang mengecek ini — baik di `05a` maupun test existing** | ❌ **Gap** | Test existing modul (`test_ac_06_*`) hanya menguji semantik field DALAM konteks modul sendiri, tidak menguji INTERAKSI dengan core (`sale.order.amount_to_invoice`, credit limit) — makanya collision ini lolos 38/38 test. AC baru + test baru diperlukan SETELAH keputusan MF-02 diambil (bentuknya tergantung opsi yang dipilih). |

## D. Cek Khusus Migrasi — P1 Fidelity

- [x] Tidak ada perubahan behavior yang tidak disengaja — semua deviasi dari source (`source-codebase`) sudah eksplisit tercatat & disetujui (manifest version bump; MF-01 test update, disetujui user)

**Cek tabrakan nama method dengan Odoo core (WAJIB):**

- [ ] ❌ **Ada tabrakan ditemukan** — `sale.order.line.amount_to_invoice`/`_compute_amount_to_invoice` (modul) vs field+method BARU dengan nama sama di core `sale` 18.0. **Dicatat sebagai CR-01 di tabel A dan `FINDINGS.md` MF-02.** Ini kolisi BARU (bukan `[DIWARISI-SOURCE]`) — field core ini tidak ada di 17.0.
- [x] Kolisi lain yang SUDAH diketahui dari baseline (F-01/`[BSL-006]`, `account.move.amount_paid` vs `account_payment`) — dikonfirmasi TETAP ADA & TIDAK BERUBAH di 18.0 (`02_DIFF_ANALYSIS.md` DIFF-02), diperlakukan sebagai `[DIWARISI-SOURCE]`, bukan temuan baru Step 8.
- [x] Method compute lain di modul ini (`_compute_amount_dp`, `_compute_waiting_for_payment_research`, `_compute_amount_received_research`, `_select_additional_fields`) dicek terhadap `native-target` — tidak ada nama yang bertabrakan dengan method/field BARU core selain `amount_to_invoice` di atas (dikonfirmasi grep `amount_received`/`waiting_for_payment` di `sale/models/sale_order_line.py` dan `sale_order.py`: no matches).

## E. Perubahan Tak Tertelusuri (di luar spec)

- [x] Tidak ada perubahan yang tidak tertelusuri ke spec — satu-satunya perubahan kode (manifest version, test MF-01) keduanya tertelusuri & disetujui.

## F. Kontribusi ke Knowledge Base

- [x] Ada — dicatat ke `migration-records/advanced_sales_analysis_17.0_18.0/SUMMARY.md`:
  - **CAND-05** (baru): Step 2 (`02_DIFF_ANALYSIS.md`) checklist "cek API yang dipakai modul stabil" TIDAK cukup — harus DITAMBAH langkah eksplisit "cek juga apakah core menambahkan field/method BARU dengan nama yang SAMA seperti field/method yang DIDEFINISIKAN modul sendiri" (bukan cuma "apakah yang modul PAKAI masih ada"). Kolisi `amount_to_invoice` (CR-01/MF-02) lolos dari Step 2 karena arah pengecekannya cuma satu arah (modul → core yang dipakai), bukan dua arah (core → field baru yang collide dengan modul).
  - **CAND-06** (baru): `sale.order.line.amount_to_invoice`/`sale.order.amount_to_invoice` (Monetary, "Un-invoiced Balance") BARU di 18.0, terhubung ke sistem credit limit partner (`account_move._compute_partner_credit`/`_get_partner_credit_warning_exclude_amount`) dan stat button `res.partner`. Modul custom APAPUN yang extend `sale.order.line`/`sale.order` dan mendefinisikan field bernama `amount_to_invoice` (nama yang cukup generik/umum dipakai) berisiko collision serupa di 18.0 — kandidat entry baru `knowledge/dependency-compat/sale_order_line/17-to-18.md` khusus soal field baru ini.

## G. Verdict

- Ringkasan Issues: 0 🔴 (CR-01 RESOLVED) · 0 🟡 · 2 🔵
- [x] ✅ **Lulus** — CR-01/MF-02 diselesaikan (2026-08-21, Opsi 2: rename `amount_to_invoice`→`asa_amount_to_invoice` di `sale.order.line`), diverifikasi ulang lewat G1 (0 failed, 0 error of 38 tests, tidak ada warning baru). Lanjut ke Step 9.
- [ ] ❌ Ditolak — N/A

**Riwayat:** Verdict awal (2026-08-21, sebelum fix) — ❌ Ditolak, 1 🔴 (CR-01). Balik ke Step 6 (edit `models/sale_report.py`, blocked sementara oleh permission `.claude/settings.json`, diselesaikan setelah user melonggarkan deny rule) → re-run G1 → review CR-01 ditutup.
