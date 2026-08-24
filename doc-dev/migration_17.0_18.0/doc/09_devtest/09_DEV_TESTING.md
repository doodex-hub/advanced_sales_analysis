# Dev Testing — advanced_sales_analysis

**Step:** 9 — Dev Testing (gate)
**Ref:** `05_acceptance/05a_MIGRATION_ACCEPTANCE_CRITERIA.md`, `05_acceptance/05b_TEST_PLAN_MIGRATION.md`, `01_intake/01b_BASELINE_SPEC.md`
**Tanggal:** 2026-08-21

---

## 9a. Audit Kesiapan Test

**1. Cek registrasi (`tests/__init__.py`):** ✅ Semua 4 file test (`common.py`, `test_account_move.py`, `test_sale_order_line.py`, `test_sale_report.py`, `test_qa_browser.py`) di-import — tidak ada file yang luput.

**2. Cek isi tiap method (AST, bukan grep nama) — dijalankan via `python3` di dalam image `odoo:18.0` (script persis dari `06a`/`09` template):**

Hasil: **38/38 method `ok`** (tidak ada satu pun `STUB`). Silang-cek tambahan: `grep -c "self\.assert"` sebelumnya (Step 5) menemukan 71 assertion tersebar di 3 file — konsisten dengan hasil AST ini.

| AC | Deskripsi | File test | Status | Catatan |
|---|---|---|---|---|
| AC-01-01, AC-01-03 | Instalasi bersih, kolisi `amount_paid` | `test_account_move.py` (3 method) | ✅ Lengkap | — |
| AC-02-02..04 | `amount_paid`/`amount_paid_cn` | `test_account_move.py` (4 method) | ✅ Lengkap | — |
| AC-03-01..04 | Komponen DP `account.move` | `test_account_move.py` (5 method) | ✅ Lengkap | — |
| (F-13, structural) | Label field duplikat | `test_account_move.py` (1 method) | ✅ Lengkap | Diperbarui rujuk `asa_amount_to_invoice` (MF-02) |
| AC-04-01..04 | `amount_received` | `test_sale_order_line.py` (7 method) | ✅ Lengkap | — |
| AC-05-01..03 | `waiting_for_payment` | `test_sale_order_line.py` (5 method) | ✅ Lengkap | — |
| AC-06-01..03 | `amount_to_invoice`/`asa_amount_to_invoice` dasar | `test_sale_order_line.py` (3 method) | ✅ Lengkap | Field di-rename MF-02, test disesuaikan |
| **AC-06-03 kritis** (F-17) | `invoice_policy` diabaikan | `test_sale_order_line.py` (1 method) | ✅ Lengkap | AC paling kritis — hasil harus `100.0` |
| **AC-06-04** (DIFF-06) | `@api.depends` melingkar | `test_sale_order_line.py` (1 method) | ✅ Lengkap | Menutup gap "belum pasti" dari Step 2 |
| AC-07-01, 02 | `sale.report` nilai & guard | `test_sale_report.py` (4 method) | ✅ Lengkap | — |
| **AC-07-03** (MF-01) | Granularitas 18.0 | `test_sale_report.py` (1 method) | ✅ Lengkap | Assertion diperbarui sesuai baseline 18.0 |
| AC-07-04 | Non-konversi mata uang | `test_sale_report.py` (1 method) | ✅ Lengkap | — |
| **AC-07-05** (gap) | UNION + `point_of_sale` | `test_sale_report.py` (1 method) | ⚠️ **Di-skip runtime** | Method ADA & lengkap (bukan stub), tapi ter-skip karena `point_of_sale` tidak terinstall di image test — lihat §Verdict |
| AC-01-02 (QA) | Measure muncul di pivot UI | `test_qa_browser.py` (1 method) | ✅ Lengkap | Chrome headless asli, bukan stub |

**Verdict audit:** ✅ Semua AC prioritas tinggi berstatus Lengkap — lanjut eksekusi. Satu AC (AC-07-05) punya test lengkap tapi tidak bisa dieksekusi penuh di environment ini (bukan gap penulisan test, gap environment) — dicatat eksplisit, tidak diam-diam diabaikan.

## Baseline

- Characterization test: 38 method sudah pernah dijalankan execution-verified terhadap **17.0** di project `doc-dev-backfill` (`doc-dev/backfill/test/04A_DEV_TESTING.md`) — hasil: 0 failed, 0 error (setelah fix F-19).
- Applicability Check Fase E (Owl/JS) dari Step 6: **Tidak, N/A** — modul tidak punya Owl/JS. `test_qa_measures_baru_tersedia_di_pivot_sales_analysis` memakai `browser_js()` (bukan `start_tour()`) karena manifest tidak punya key `assets` (`[BSL-022]`/F-18) — tetap Chrome headless ASLI, bukan simulasi.

## Hasil Unit, Integration & Tour Test (target-codebase, Odoo 18.0)

> Dieksekusi Step 6 (G1, 4 percobaan — lihat `06_implementation/06c_IMPLEMENTATION_LOG.md`) dan diverifikasi ulang di sini sebagai bagian gate Step 9 formal. Command: `MSYS_NO_PATHCONV=1 docker compose up` (`--test-enable --test-tags=/advanced_sales_analysis`), Mode C (AI jalankan langsung).
>
> **Verifikasi anti-false-pass (lesson `crm_probability_from_stage`):** jumlah baris log `Starting <Class>.<method>` dicocokkan = **38**, persis jumlah method test yang ada — bukan `0 tests` yang menyamar sukses.

| AC | Unit | Integration | Tour (N/A — Fase E N/A) | Pass/Fail | Catatan |
|---|---|---|---|---|---|
| AC-01, AC-02, AC-03 (`account.move`) | ✅ | — | N/A | ✅ Pass | 13 method, `test_account_move.py` |
| AC-04, AC-05, AC-06 (`sale.order.line`) | ✅ | ✅ (`_invoice_so`/`_pay` helper melibatkan `account.move`) | N/A | ✅ Pass | 17 method, `test_sale_order_line.py`, termasuk AC-06-03 kritis (`100.0`, bukan regresi F-17) dan AC-06-04 (circular depends, tidak ada order-dependency di 18.0) |
| AC-07 (`sale.report`) | ✅ | ✅ (SQL view lintas `sale.order.line`/`account.move`) | N/A | ✅ Pass (6/7) · ⚠️ Skip (1/7) | 7 method. AC-07-03 (MF-01, granularitas 18.0) pass sesuai baseline baru. **AC-07-05 (`test_f19_union_kompatibel_dengan_point_of_sale`) di-skip** — `point_of_sale` tidak terinstall di image `odoo:18.0` test ini. |
| AC-01-02 (QA browser) | — | ✅ (Chrome headless, `browser_js`) | N/A | ✅ Pass | 1 method, `test_qa_browser.py` — "test successful" dikonfirmasi di log |

**Ringkasan eksekusi final (percobaan G1 #4, setelah fix MF-01 & MF-02):** `0 failed, 0 error(s) of 38 tests`. Tidak ada warning baru di luar yang sudah didokumentasikan (F-13 label collision, chrome_crashpad zombie cleanup — benign).

## Kontribusi ke Knowledge Base

- [x] Ada — sudah dicatat sebelumnya di Step 6/8 (`migration-records/advanced_sales_analysis_17.0_18.0/SUMMARY.md` CAND-01 s/d CAND-06): kolisi `account_payment`/`amount_to_invoice` dengan core, alias `_group_by_sale()` berubah, checklist tabrakan nama dua-arah, dan gotcha permission `.claude/settings.json`. Tidak ada temuan BARU di Step 9 sendiri di luar yang sudah tercatat.

## Verdict

- [x] ✅ **Semua AC prioritas Unit/Integration pass** — lanjut ke Step 10 (QA Testing).
- **Gap terbuka yang dibawa ke Step 10/11 (bukan blocker Step 9):** AC-07-05 (test UNION+POS) tetap tidak terverifikasi eksekusi penuh di lingkungan mana pun (17.0 maupun 18.0) karena `point_of_sale` tidak pernah terinstall bersamaan di image test manapun yang dipakai sejauh ini. Kalau QA (Step 10) atau environment produksi punya POS terinstall, ini kesempatan menutup gap ini — dicatat eksplisit di `05b_TEST_PLAN_MIGRATION.md` dan di sini, bukan diam-diam dianggap selesai.
