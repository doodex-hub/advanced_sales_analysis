# Business Flow — Migrasi advanced_sales_analysis

**Step:** 10 — QA Testing (gate)
**Versi:** 19.0 → 20.0
**Ref:** `01_intake/01b_BASELINE_SPEC.md`, `05_acceptance/05a_MIGRATION_ACCEPTANCE_CRITERIA.md`, `05_acceptance/05b_TEST_PLAN_MIGRATION.md`
**Tanggal:** 2026-09-24

Environment QA: `docker-env/` Odoo 20.0 (`migration/20.0` commit `83e8719`), DB `advanced_sales_analysis_test_20` (modul + `pos_sale` terinstall dari Run C, tanpa demo data). Pembanding 19.0: snapshot `git archive migration/19.0` di image `advanced_sales_analysis_migration_19-odoo` (`odoo:19.0`), DB baru `asa19` — **Cross-Version Compare A/B** dengan skrip seed yang SAMA (`scratchpad/qa_seed.py`: 3 SO — lunas, dibayar 200/500, belum difakturkan). Stack 19.0 dibongkar lagi setelah perbandingan (`down -v`).

Batasan eksekusi: AI tidak mengetik password login di browser (aturan keamanan sesi). Lapisan UI dibuktikan oleh `HttpCase.browser_js` (Chrome headless asli, login di sisi server test) di Run A/B/C; lapisan data/pivot dibuktikan lewat `formatted_read_group` — query agregasi yang sama yang dikirim pivot.

---

## Skenario

### S-01: Instalasi bersih & Sales Analysis pivot dengan measure modul terbuka tanpa error
**Level:** Smoke
**Provenance:** `[DIKONFIRMASI]`
**AC:** AC-01-01, AC-01-02
**Langkah:** install modul di DB baru → Sales → Reporting → Sales → Pivot → Measures → Amount Received.
**Hasil 20.0:** install sukses (Run A/B/C, modul `installed`, 41 method test berjalan); `browser_js` membuka pivot, dropdown berisi "Amount Received", "Waiting for Payment", "Amount To Invoice", kolom Amount Received tampil — PASS.
**Pembanding:** sebelum fix (probe Step 2) langkah yang sama → HTTP 500 `function sum(text) does not exist`. 19.0: PASS (G1 18→19).
**Status:** ✅ Pass

### S-02: Tiga measure bernilai identik 19.0 untuk alur SO → faktur → pembayaran
**Level:** Main Flow
**Provenance:** `[DIKONFIRMASI]` (A/B live, dua versi)
**AC:** AC-04-01, AC-04-03, AC-05-01, AC-05-02, AC-06-01, AC-06-02, AC-07-01
**Langkah:** seed 3 SO (A: 1000 lunas; B: 500 dibayar 200; C: 1000+500 dikonfirmasi belum difakturkan) → baca per baris SO → agregasi `sale.report` per order & total.

| Data | 19.0 | 20.0 |
|---|---|---|
| SO A baris (received, waiting, to invoice) | 1000 / 0 / 0 | 1000 / 0 / 0 |
| SO B baris | 200 / 300 / 0 | 200 / 300 / 0 |
| SO C baris (2) | 0/0/1000, 0/0/500 | 0/0/1000, 0/0/500 |
| `sale.report` total (received / waiting / to invoice) | 1200 / 300 / 1500 | 1200 / 300 / 1500 |
| Agregasi pivot 20.0 per order (`formatted_read_group` group by `name`) | — | S00031 1000/0/0 · S00032 200/300/0 · S00033 0/0/1500 |

**Status:** ✅ Pass — identik.

### S-03: Uang muka, credit note, mata uang lain, pajak `price_include`
**Level:** Detail
**Provenance:** `[DIKONFIRMASI]` (test otomatis di instance 20.0 hidup, Run A/B/C)
**AC:** AC-03-*, AC-04-05/06, AC-06-03b, AC-06-04, AC-07-04
**Hasil:** semua PASS, termasuk quirk yang WAJIB dipertahankan: 2 baris DP → hanya terakhir (AC-03-03), DP `partial` dianggap belum dibayar (AC-03-04), `invoice_policy=delivery` → 100 bukan 40 (AC-06-04), kolom modul tidak dikonversi kurs (core 50 vs modul 100, AC-07-04).
**Status:** ✅ Pass

### S-04: Sales Analysis dengan `pos_sale` terinstall
**Level:** Detail
**Provenance:** `[DIKONFIRMASI]` untuk query UNION (Run C `test_f19_*` + agregasi S-02 dijalankan di DB yang sama dengan `pos_sale` terinstall); `[HASIL-BACA]` untuk nilai `amount_to_invoice` di baris POS (MF-02 — tidak ada POS order dibuat)
**AC:** AC-07-05
**Hasil:** laporan terbuka & agregasi benar dengan `pos_sale` terinstall. Perbedaan nilai baris POS (MF-02) diterima dev.
**Status:** ✅ Pass (dengan catatan MF-02)

### S-05: Granularitas baris laporan (perubahan core)
**Level:** Detail
**Provenance:** `[DIKONFIRMASI]` (`test_ac_07_03`, `test_ac_07_03b`)
**AC:** AC-07-03, AC-07-03b
**Hasil:** harga beda → 2 baris (identik 19.0); deskripsi beda → 2 baris (20.0, MF-03 diterima); total tetap.
**Status:** ✅ Pass

### S-06: Regresi hook lama tidak muncul lagi / baris tanpa produk
**Level:** Negative
**Provenance:** `[DIKONFIRMASI]`
**AC:** AC-07-02, AC-07-06
**Hasil:** baris section tidak masuk laporan; `sale.report` tidak punya `_select_additional_fields`, 3 kolom modul ada di `_select_dict` tanpa kurs; tipe field `float`, aggregator `sum` (bukan text — penyebab crash probe).
**Status:** ✅ Pass

## Ringkasan per Level

| Level | Skenario | Jumlah |
|---|---|---|
| Smoke | S-01 | 1 |
| Main Flow | S-02 | 1 |
| Detail | S-03, S-04, S-05 | 3 |
| Negative | S-06 | 1 |

## Rekap Provenance

| Provenance | Jumlah | Skenario |
|---|---|---|
| `[DIKONFIRMASI]` | 6 | S-01…S-06 (S-04 sebagian) |
| `[HASIL-BACA]` | 1 (sebagian) | S-04 nilai baris POS |
| `[HASIL-BACA-MURNI]` | 0 | — |
| `[PERLU-KEPUTUSAN]` | 0 | — |

## Human QA Checklists

`human_qa/` (00_README, 01_SMOKE, 02_MAIN_FLOW, 03_DETAIL, 04_NEGATIVE) — untuk re-verifikasi manual oleh dev/QA/PM tanpa AI.

## Loop-back

Tidak ada — tidak ada skenario Fail.

## Verdict

- [x] ✅ Lulus (2026-09-24) — 6/6 skenario Pass, paritas A/B 19.0↔20.0 identik.
