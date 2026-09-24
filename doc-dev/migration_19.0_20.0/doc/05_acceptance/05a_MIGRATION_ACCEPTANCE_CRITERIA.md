# Migration Acceptance Criteria — advanced_sales_analysis

**Step:** 5 — Acceptance Criteria & Test Plan
**Ref:** `01_intake/01b_BASELINE_SPEC.md` dan kode 19.0 yang berjalan (`migration/19.0`) — **bukan** `03_spec/03_MIGRATION_SPEC.md`
**Tanggal:** 2026-09-24

> **Then** = perilaku yang harus IDENTIK antara 19.0 (baseline) dan 20.0. Diturunkan 1:1 dari AC 18→19 (`doc-dev/migration_18.0_19.0/doc/05_acceptance/05a_MIGRATION_ACCEPTANCE_CRITERIA.md`, execution-verified 39/39), ID dipertahankan. Kolom "Test" = test otomatis di `advanced_sales_analysis/tests/`. AC yang terkait risiko tinggi `03_MIGRATION_SPEC.md` ditandai **[RISIKO-TINGGI]**.

---

## AC-01 — Instalasi & registrasi field (verifies `[BSL-005]`, `[BSL-001]`–`[BSL-003]`)

**AC-01-01** [RISIKO-TINGGI — Critical Blocker #1]
Given database Odoo 20.0 dengan `sale`, `account`, `sale_management`
When modul diinstall
Then instalasi sukses (modul `installed`, bukan `installable=False`), test modul benar-benar dijalankan (jumlah test > 0), kolom `amount_received`/`amount_to_invoice`/`waiting_for_payment` ada di view `sale_report`; tidak ada error, warning hanya yang sudah diketahui (BSL-017 "same label").
Test: log G1 + semua test (implisit).

**AC-01-02** [RISIKO-TINGGI — Critical Blocker #2]
Given modul terinstall
When user membuka Sales → Reporting → Sales Analysis, pindah ke Pivot, membuka *Measures* dan memilih *Amount Received*
Then ketiga measure muncul di dropdown DAN kolom *Amount Received* tampil di pivot tanpa error server — identik 19.0.
Test: `test_qa_browser.test_qa_measures_baru_tersedia_di_pivot_sales_analysis`.

## AC-02 — Kolisi `amount_paid` dengan `account_payment` (verifies `[BSL-006]`)

**AC-02-01** Given `account_payment` ikut terinstall, When registry dibangun, Then `account.move.amount_paid` = definisi modul (Float stored), semantik modul (bukan `transaction_ids`). Test: `test_ac_01_03_*` (3 test).
**AC-02-02** Given `out_invoice` 100 dibayar penuh, Then `amount_paid == 100`. Test: `test_ac_02_01_*`.
**AC-02-03** Given `out_refund` dibayar, Then `amount_paid_cn == amount_total − amount_residual`. Test: `test_ac_02_02_*`.
**AC-02-04** Given `entry`/`in_invoice`/`out_invoice not_paid`, Then `amount_paid`/`amount_paid_cn` = 0.0, tanpa error. Test: `test_ac_02_03_*`, `test_ac_02_04_*`.

## AC-03 — Komponen uang muka `account.move` (verifies `[BSL-007]`, `[BSL-011]`, `[BSL-013]`, `[BSL-017]`)

**AC-03-01** DP positif belum dibayar → `amount_dp2_nopaid == price_subtotal`, `amount_dp2 == 0`. Test: `test_ac_03_01_*`.
**AC-03-02** DP negatif sudah dibayar → masuk `amount_dp`. Test: `test_ac_03_02_*`.
**AC-03-03** Dua baris DP → hanya baris terakhir (bug dipertahankan). Test: `test_ac_03_03_*`.
**AC-03-04** DP `partial` → dianggap belum dibayar (inkonsistensi dipertahankan). Test: `test_ac_03_04_*`.
**AC-03-05** Produk DP non-Inggris ("Acompte") → tidak dikenali. Test: `test_ac_03_05_*`.
**AC-03-06** Label duplikat tetap (BSL-017). Test: `test_f13_label_field_duplikat`.

## AC-04 — `sale.order.line.amount_received` (verifies `[BSL-010]`, `[BSL-020]`)

**AC-04-01** lunas 100 → 100. **AC-04-02** belum dibayar → 0. **AC-04-03** dibayar 60 → 60. **AC-04-04** dua baris proporsional. **AC-04-05** credit note mengurangi. **AC-04-06** baris DP pakai jalur `amount_dp`. **AC-04-07** `amount_untaxed == 0` tidak error, kontribusi 0.
Test: `test_ac_04_01`…`test_ac_04_07`.

## AC-05 — `sale.order.line.waiting_for_payment` (verifies `[BSL-009]`)

**AC-05-01** difakturkan belum dibayar → 100. **AC-05-02** dibayar 60 → 40. **AC-05-03** belum difakturkan → 0. **AC-05-04** faktur cancel diabaikan. **AC-05-05** dua faktur untuk satu baris.
Test: `test_ac_05_01`…`test_ac_05_05`.

## AC-06 — `sale.order.line.asa_amount_to_invoice` (verifies `[BSL-008]`, `[BSL-021]`, `[BSL-024]`)

**AC-06-01** belum difakturkan → 100. **AC-06-02** lunas → 0. **AC-06-03** draft SO → 0.
**AC-06-04** `invoice_policy == 'delivery'`, qty 10 delivered 4 → **100.0, BUKAN 40.0** (dead-code path dipertahankan; hasil 40.0 = REGRESI, eskalasi).
**AC-06-03b** pajak `price_include` + diskon beda → compute via `tax_ids.compute_all()` sukses dan angka identik 19.0.
**AC-06-05** urutan pembacaan field melingkar tidak mempengaruhi hasil.
Test: `test_ac_06_01`…`test_ac_06_05`, `test_ac_06_03b_*`.

## AC-07 — `sale.report` (verifies `[BSL-005]`, `[BSL-014]`, `[BSL-023]`) — **seluruh grup bergantung pada fix DIFF-01/MF-01**

**AC-07-01** [RISIKO-TINGGI] Given SO dengan `amount_received = 100`, When `sale.report` dibaca (setelah `flush_all()`), Then `amount_received == 100`; `waiting_for_payment`/`amount_to_invoice` juga sama dengan nilai baris SO. Test: `test_ac_07_01_*`, `test_ac_07_01b_*`, `test_ac_07_01c_*`.
**AC-07-02** Baris section/note tidak masuk view (core `display_type` filter). Test: `test_ac_07_02_*`.
**AC-07-03** Dua baris produk sama, harga beda → 2 row (granularitas core). Test: `test_ac_07_03_group_by_granularitas_18_0`.
**AC-07-03b** (BARU, MF-03 — perubahan core yang diterima, BUKAN identik 19.0) Given dua baris produk & harga sama, deskripsi beda, Then 2 row di 20.0 (19.0: 1 row); total `amount_received`/`price_subtotal` tetap = jumlah kedua baris. Test: `test_ac_07_03b_group_by_nama_baris_20_0` (baru).
**AC-07-04** [RISIKO-TINGGI] SO mata uang lain (kurs 2) → `price_subtotal` core dikonversi (50), `amount_received` TIDAK (100). Test: `test_ac_07_04_*`.
**AC-07-05** (gap warisan, tetap terbuka) UNION dengan `pos_sale` terinstall: query sukses. Di 20.0 ditambah catatan MF-02 (baris POS mengisi `amount_to_invoice`). Test: `test_f19_union_kompatibel_dengan_point_of_sale` (skip tanpa POS).
**AC-07-06** (BARU, regression guard DIFF-01) `sale.report` tidak lagi punya `_select_additional_fields`; `_select_dict()` berisi 3 key modul dengan ekspresi `SUM` tanpa kurs. Test: `test_ac_07_06_select_dict_hook_dipakai` (baru).

---

## Ringkasan Traceability

38 AC tercakup oleh 41 method test otomatis (39 lama + 2 baru). Catatan: runner Odoo 20 sudah melaporkan "41 tests" untuk 39 method lama di probe Step 2 — angka runner ≠ jumlah method; Step 9 mencatat keduanya. BSL tanpa AC eksekutif (sama seperti 18→19): BSL-004 (tercakup AC-03/04), BSL-012, BSL-015, BSL-016, BSL-018, BSL-019, BSL-022 (struktural). AC yang BUKAN "identik 19.0" (perubahan disengaja/diterima, tercatat di FINDINGS): AC-07-03b (MF-03), catatan AC-07-05 (MF-02).
