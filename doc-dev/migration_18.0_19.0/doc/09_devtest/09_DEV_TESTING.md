# Dev Testing — advanced_sales_analysis

**Step:** 9 — Dev Testing (gate)
**Ref:** `05_acceptance/05a_MIGRATION_ACCEPTANCE_CRITERIA.md`, `05_acceptance/05b_TEST_PLAN_MIGRATION.md`, `01_intake/01b_BASELINE_SPEC.md`
**Tanggal:** 2026-08-26

---

> **Eksekusi:** `docker compose up` di `docker-env/` (Mode C, AI jalankan langsung, environment Claude Code CLI) — command di dalam `docker-compose.yml` SUDAH persis `odoo -i advanced_sales_analysis --test-enable --test-tags=/advanced_sales_analysis --stop-after-init`, sama dengan yang diwajibkan step ini. **Run ini SUDAH dieksekusi di Step 6 sebagai checkpoint G1** (`06_implementation/06c_IMPLEMENTATION_LOG.md`, "Riwayat Percobaan G1" #1) — tidak ada perubahan kode APAPUN sejak run itu (Step 7 N/A, Step 8 tidak mengubah kode), jadi hasil G1 dipakai LANGSUNG di sini sebagai hasil eksekusi Step 9, bukan diulang percuma. Kalau Step 8/review manapun nanti mengubah kode, run ini WAJIB diulang sebelum gate ditutup — belum terjadi di project ini.
>
> **Bahaya MSYS `--test-tags`:** TIDAK relevan di run ini — `--test-tags` ada di dalam string `command:` YAML `docker-compose.yml`, bukan diketik langsung sebagai argumen Bash (`docker compose up` tidak membawa argumen `--test-tags` di command line-nya) — jadi tidak lewat parsing MSYS Git Bash sama sekali. Dikonfirmasi TIDAK terjadi false-pass "0 tests": log `odoo.tests.result` eksplisit menyebut **39 tests** (bukan 0), cocok dengan jumlah method test yang benar-benar ada (lihat 9a).

## 9a. Audit Kesiapan Test

**1. Registrasi (`tests/__init__.py`):** meng-import semua 4 file test (`common`, `test_account_move`, `test_sale_order_line`, `test_sale_report`, `test_qa_browser`) — tidak ada file test yang tidak ter-load.

**2. Audit isi tiap method (bukan cuma nama):**

| File | Jumlah `def test_*` | Hasil audit |
|---|---|---|
| `test_account_move.py` | 13 | ✅ Lengkap — 32 baris assert (`assertAlmostEqual`/`assertEqual`), verifikasi behavior nyata (AC-02, AC-03) |
| `test_sale_order_line.py` | 18 | ✅ Lengkap — 28 baris assert (termasuk `test_ac_06_03b_tax_ids_rename_price_include` yang baru), verifikasi AC-04/05/06 |
| `test_sale_report.py` | 7 | ✅ Lengkap — 13 baris assert, verifikasi AC-01/AC-07 |
| `test_qa_browser.py` | 1 | ✅ Lengkap (bukan stub, walau 0 baris `assert*` Python) — test `browser_js` Chrome headless nyata, verifikasi via `throw new Error(...)`/`console.error` di JS yang diinjeksikan (dibaca manual, dikonfirmasi bukan pola stub `ast` docstring-only) |

**Total: 39 method test, SEMUA berstatus Lengkap — 0 Stub, 0 Tidak valid, 0 Tidak ada** untuk AC yang memang diberi AC eksekutif di `05a` (12 dari 23 `BSL-NNN`, sisanya sengaja tidak diberi AC eksekutif sejak migrasi 17→18, lihat `05a` §Ringkasan Traceability).

**Verdict audit (sebelum eksekusi):**
- [x] Semua AC prioritas tinggi (`AC-06-03` dead-code F-17, `AC-06-03b` fix DIFF-01 baru, `AC-07-03` granularitas) berstatus Lengkap — lanjut ke eksekusi (sudah dieksekusi di G1, lihat di atas)
- [ ] Ada AC prioritas tinggi berstatus Stub/Tidak ada

## Baseline

- Characterization test: modul ini SUDAH execution-verified 2x sebelumnya (proyek `doc-dev-backfill` untuk 17.0, migrasi 17→18 untuk 18.0) — baseline behavior 18.0 didokumentasikan penuh di `01b_BASELINE_SPEC.md`, bukan hasil dugaan.
- Applicability Check Fase E (Owl/JS): **Tidak, N/A** (`01a_MIGRATION_INTAKE.md` §2b) — modul tidak punya file `.js` sama sekali. `test_qa_browser.py` BUKAN Tour test Owl (tidak butuh key `assets` manifest, lihat docstring file itu) — ini `HttpCase.browser_js()` yang menguji UI generik (pivot Sales Analysis) tanpa menyentuh kode Owl custom modul ini. Tidak ada tour test yang "seharusnya ada tapi hilang".

## Hasil Unit, Integration & Tour Test (target-codebase, Odoo 19.0)

| AC | Unit | Integration | Tour (N/A — lihat Baseline) | Pass/Fail | Catatan |
|---|---|---|---|---|---|
| AC-01-01/02 | `test_ac_01_*` (`test_sale_report.py`) | — | `test_qa_measures_baru_tersedia_di_pivot_sales_analysis` (`test_qa_browser.py`) | ✅ Pass | Bagian dari 39/39 |
| AC-02-01..04 | `test_account_move.py::test_ac_02_*` | — | — | ✅ Pass | Bagian dari 39/39 |
| AC-03-01..04 | `test_account_move.py::test_ac_03_*` | — | — | ✅ Pass | Bagian dari 39/39 |
| AC-04-01..07 | `test_sale_order_line.py::test_ac_04_*` | — | — | ✅ Pass | Bagian dari 39/39 |
| AC-05-01..05 | `test_sale_order_line.py::test_ac_05_*` | — | — | ✅ Pass | Bagian dari 39/39 |
| AC-06-01..04 | `test_sale_order_line.py::test_ac_06_01..05` | — | — | ✅ Pass | Termasuk `test_ac_06_04_invoice_policy_delivery_diabaikan` (dead-code F-17 dipertahankan, `100.0` bukan `40.0` — bukan regresi) |
| **AC-06-03b** | `test_ac_06_03b_tax_ids_rename_price_include` | — | — | ✅ **Pass** | Verifikasi POSITIF fix DIFF-01 — hasil `100.0` (110 gross − 10% pajak included), tidak `AttributeError` |
| AC-07-01..04 | `test_sale_report.py::test_ac_07_01..04` | `test_sale_report.py` (butuh `flush_all()`, lintas model) | — | ✅ Pass | Termasuk `test_ac_07_03_group_by_granularitas_18_0` (granularitas 2-row, stabil 18.0→19.0 per DIFF-02) |
| AC-07-05 | — | **Tidak dieksekusi** | — | ⚠️ **Gap tetap terbuka** | `point_of_sale`/`pos_sale` tidak terinstall di `docker-compose.yml` G1 — konsisten gap yang sudah didokumentasikan sejak `05a`/migrasi 17→18, BUKAN regresi baru. Analisis statis (`02_DIFF_ANALYSIS.md` DIFF-05) tetap satu-satunya bukti untuk item ini. |

**Ringkasan eksekusi:** `0 failed, 0 error(s) of 39 tests` (`docker-env/logs/odoo.log:990`, 2026-08-26). Tidak ada loop fix→retest yang diperlukan — semua lulus di percobaan pertama (rename DIFF-01 sudah benar sejak Step 6, tidak ada regresi dari perubahan lain karena tidak ada perubahan lain).

## Kontribusi ke Knowledge Base

- [x] Tidak ada temuan baru — hasil test 100% sesuai ekspektasi yang sudah dianalisis Step 2/3, tidak ada perilaku Odoo 19.0 yang mengejutkan di luar DIFF-01 yang sudah diketahui.

## Verdict

- [x] ✅ **Semua AC prioritas Unit/Integration pass** — lanjut ke step 10. (AC-07-05 tetap gap terbuka yang sudah diketahui & disetujui sebagai keterbatasan testing, bukan kegagalan yang memblokir gate — konsisten keputusan yang sama di migrasi 17→18.)
- [ ] ❌ Ada yang gagal
