# Dev Testing — advanced_sales_analysis

**Step:** 9 — Dev Testing (gate)
**Ref:** `05_acceptance/05a_MIGRATION_ACCEPTANCE_CRITERIA.md`, `05_acceptance/05b_TEST_PLAN_MIGRATION.md`, `01_intake/01b_BASELINE_SPEC.md`
**Tanggal:** 2026-09-24

---

## 9a. Audit Kesiapan Test

1. **Registrasi:** `tests/__init__.py` meng-import `common`, `test_account_move`, `test_sale_order_line`, `test_sale_report`, `test_qa_browser` — semua file `test_*.py` ter-load (dibuktikan: 41 method "Starting …" di log).
2. **Isi method:** audit AST (dijalankan di container, Python 3.12, 2026-09-24): **41 method, 0 stub**. Tidak ada test stale — satu-satunya assertion yang bergantung pada perilaku core (`test_ac_07_03`) tetap valid di 20.0.
3. **Cross-reference AC:**

| AC | Deskripsi | File test | Status | Catatan |
|---|---|---|---|---|
| AC-01-01 | install + test jalan | log G1 | ✅ Lengkap | Guard "0 tests" dicek eksplisit |
| AC-01-02 | measure di pivot | `test_qa_browser.py` | ✅ Lengkap | Chrome headless asli |
| AC-02-* | kolisi `amount_paid` | `test_account_move.py` | ✅ Lengkap | 5 method |
| AC-03-* | DP | `test_account_move.py` | ✅ Lengkap | 8 method |
| AC-04-*, AC-05-*, AC-06-* | compute SOL | `test_sale_order_line.py` | ✅ Lengkap | 18 method |
| AC-07-01…04, 03b, 06 | `sale.report` | `test_sale_report.py` | ✅ Lengkap | 8 method |
| AC-07-05 | UNION POS | `test_sale_report.py::test_f19_*` | ✅ Lengkap (butuh POS) | Run C |

**Verdict audit:** semua AC risiko tinggi berstatus Lengkap → lanjut eksekusi.

## Baseline

- Test karakterisasi source (sama lokasi dengan source, `advanced_sales_analysis/tests/`). Hasil terhadap source 19.0: G1 migrasi 18→19 `0 failed, 0 error(s) of 39 tests` (2026-08-26, image `odoo:19.0`).
- Bukti bahwa test lama benar-benar menangkap regresi 20.0: probe Step 2 (kode 19.0 + versi di-bump saja) → **5 FAIL** (AC-07-01/01b/01c/04 + AC-01-02). Setelah fix A5 → PASS. Jadi test tidak lulus secara kosong.
- Applicability Fase E: N/A → tidak ada tour test wajib; `browser_js` dipakai sebagai lapisan UI.

## Hasil Unit, Integration & Browser Test (target-codebase, `migration/20.0` commit `83e8719`)

| Run | Environment | Hasil runner | Method dijalankan | Skip |
|---|---|---|---|---|
| A | Community `odoo20`, postgres:15 | **0 failed, 0 error(s) of 43 tests** | 41 | 1 (`test_f19_*`, POS tidak terinstall) |
| B | Community + `enterprise20` di addons-path (92 modul, `web_enterprise` ter-load), postgres:16 | **0 failed, 0 error(s) of 43 tests** | 41 | 1 (`test_f19_*`) |
| C | Community + `pos_sale` (`-i advanced_sales_analysis,pos_sale`), postgres:16 | **0 failed, 0 error(s) of 43 tests** | 41 | **0 — `test_f19_*` DIJALANKAN** |

Catatan angka: runner Odoo 20 menghitung 43 "tests" untuk 41 method (selisih dari hitungan internal runner `HttpCase`/subtest — sama-sama muncul di probe 41 vs 39 method); yang dicatat sebagai bukti adalah 41 method "Starting" + 0 failed/0 error.

Warning di log (semua sudah diketahui, bukan regresi): BSL-017 "same label" (juga muncul di `account.bank.statement.line` via `_inherits` — sama seperti 19.0), `markdown2 is not installed` (lingkungan), Postgres < 16 (Run A saja → compose dinaikkan ke 16).

| AC | Unit | Integration | Browser | Pass/Fail | Catatan |
|---|---|---|---|---|---|
| AC-01-01 | — | G1 A/B/C | — | ✅ | |
| AC-01-02 | — | — | `browser_js` | ✅ | A/B/C |
| AC-02-*, AC-03-* | 13 | — | — | ✅ | |
| AC-04-*, AC-05-*, AC-06-* | 18 | — | — | ✅ | AC-06-04 = 100.0 (dead-code path dipertahankan) |
| AC-07-01…04, 03b, 06 | — | 8 (SQL view nyata) | — | ✅ | |
| AC-07-05 | — | `test_f19_*` (Run C) | — | ✅ | **Gap warisan sejak 17.0 TERTUTUP** — UNION dengan `pos_sale` dieksekusi nyata pertama kali |

## Kontribusi ke Knowledge Base

- [x] Ada — `migration-records/advanced_sales_analysis_19.0_20.0/SUMMARY.md`: CAND-07 (Postgres 16), CAND-09 (MSYS mangling env var compose).

## Verdict

- [x] ✅ Lulus (2026-09-24) — 0 failed/0 error di 3 environment, semua AC tercakup, AC-07-05 tertutup.
