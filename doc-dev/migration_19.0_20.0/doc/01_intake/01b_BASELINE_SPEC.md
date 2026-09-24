# Baseline Spec — advanced_sales_analysis

**Step:** 1 — Intake & Scope (pelengkap `01a_MIGRATION_INTAKE.md`)
**Tujuan:** dokumentasikan APA yang modul lakukan (behavior as-is) di **19.0** — sumber kebenaran untuk `05a_MIGRATION_ACCEPTANCE_CRITERIA.md` dan semua testing migrasi 19→20 (step 9/10/11).
**Tanggal:** 2026-09-24
**Sumber:** Direkonsiliasi dari `doc-dev/migration_18.0_19.0/doc/01_intake/01b_BASELINE_SPEC.md` (baseline 18.0, `BSL-NNN`) + `doc-dev/migration_18.0_19.0/doc/FINDINGS.md` (MF-01 18→19, RESOLVED — sekarang bagian baseline 19.0) + cross-check langsung ke kode branch `migration/19.0` (HEAD `45c0319`), dibaca 2026-09-24. Test karakterisasi: `advanced_sales_analysis/tests/` (39 test, sama lokasi dengan source), G1 terakhir di 19.0 `0 failed, 0 error(s) of 39 tests` (2026-08-26).

> Semua klaim di-cross-check ulang ke kode `migration/19.0` — cocok, tidak ada penyimpangan baru. Semua `[MATCH]`. ID `BSL-NNN` melanjutkan skema project sebelumnya (nomor sama = klaim sama). Satu ID baru: `[BSL-024]` (fakta baseline 19.0 yang lahir dari migrasi 18→19).

---

## Provenance Tag

`[MATCH]`/`[GAP]`/`[NO-SPEC]` — standar `migration-tool`. `(ref: MF-NN 18→19)` = finding migrasi 18→19 yang sudah resolved.

---

## Ringkasan untuk Review — Perlu Konfirmasi User

**Tally:** 24 `[BSL-NNN]`, semua `[MATCH]` (0 `[GAP]`, 0 `[NO-SPEC]`).

1. **`[BSL-005]` dan `[BSL-023]` bergantung pada hook `sale.report._select_additional_fields()`** — hook ini TIDAK ADA lagi di core 20.0 (lihat `01a` Ringkasan poin 3, detail di `02_DIFF_ANALYSIS.md` DIFF-01). Behavior yang harus dipertahankan adalah ISI & SEMANTIK kolomnya (SUM per grup, guard `product_id IS NOT NULL`, tanpa konversi mata uang — BSL-014), bukan nama hook-nya.
2. **`[BSL-006]` kolisi `account.move.amount_paid` dengan `account_payment`** — masih ada di 20.0 (definisi `account_payment.amount_paid` 20.0 identik dengan 19.0: Monetary non-stored dari `transaction_ids`). Dipertahankan.
3. **`[BSL-024]` baru:** `sale.order.line.tax_ids` (rename 18→19) adalah baseline 19.0; field ini masih bernama sama di 20.0.
4. **Granularitas GROUP BY `sale.report`** (`[BSL-023]` poin 2) mengikuti core — baseline 19.0 = kolom GROUP BY core 19.0. Kalau core 20.0 mengubahnya, itu perubahan core yang otomatis ikut (preseden MF-01 17→18, disetujui pemilik modul) — dicatat di Step 2, bukan diperbaiki balik.
5. 15 quirk (§8) tetap terbuka dan wajib identik di 20.0. Gap AC-07-05 (UNION dengan POS terinstall) tetap belum pernah dieksekusi.

---

## 1. Tujuan Modul

Modul memperkaya laporan **Sales Analysis** (`sale.report`) dengan tiga metrik finansial: **Amount Received** (uang yang sudah diterima per baris penjualan), **Waiting for Payment** (sudah difakturkan, belum dibayar), **Amount To Invoice** (belum difakturkan — field internal `sale.order.line.asa_amount_to_invoice`, lihat `[BSL-008]`).

`sale.report` adalah SQL view (`_auto=False`) yang membaca tabel `sale_order_line` langsung, jadi ketiga metrik dihitung dulu sebagai field stored-compute di `sale.order.line`, lalu ditarik ke SQL view lewat hook `_select_additional_fields()` (19.0). Perhitungan bertumpu pada 8 field bantu stored-compute di `account.move`.

## 2. Model & Tanggung Jawab

| Model | Tanggung Jawab |
|---|---|
| `sale.report` (`_inherit`) | Tambah 3 kolom agregat read-only lewat `_select_additional_fields()`. |
| `account.move` (`_inherit`) | 8 field stored-compute: komponen dibayar/belum-dibayar/uang-muka/retur. |
| `sale.order.line` (`_inherit`) | 3 field stored-compute (`amount_received`, `waiting_for_payment`, `asa_amount_to_invoice`). |

Tidak ada model baru, tidak ada view/XML (`'data': []`).

## 3. Field dengan Makna Bisnis

### `sale.report`
- `amount_received` (Float, readonly, label "Amount Received") — `SUM(l.amount_received)`.
- `amount_to_invoice` (Float, readonly, label "Amount To Invoice") — `SUM(l.asa_amount_to_invoice)`.
- `waiting_for_payment` (Float, readonly, label "Waiting for Payment") — `SUM(l.waiting_for_payment)`.

### `account.move`
- `amount_paid` / `amount_paid_cn` (Float, compute `_compute_amount_paid`, store) — kolisi dengan `account_payment` (`[BSL-006]`).
- `amount_dp` / `amount_dp2` / `amount_dp_nopaid` / `amount_dp2_nopaid` (Float, compute `_compute_amount_dp`, store).
- `amount_refund` / `amount_refund_nopaid` (Float, compute `_compute_amount_dp`, store).

### `sale.order.line`
- `amount_received` (Float, compute `_compute_amount_received_research`, store).
- `waiting_for_payment` (Float, compute `_compute_waiting_for_payment_research`, store).
- `asa_amount_to_invoice` (Float, compute `_compute_asa_amount_to_invoice`, store, label "Amount Received" — salah, `[BSL-017]`).

## 4. Business Workflow (User Stories)

- `[BSL-001]` `[MATCH]` Sales manager membuka **Sales → Reporting → Sales Analysis**, menambah measure *Amount Received*.
- `[BSL-002]` `[MATCH]` Finance menambah measure *Waiting for Payment*.
- `[BSL-003]` `[MATCH]` Finance menambah measure *Amount To Invoice*.
- `[BSL-004]` `[MATCH]` Baris "Down payment" tidak boleh menggandakan/menghilangkan angka (deteksi: `[BSL-013]`).

Tidak ada state-transition/action button/wizard.

## 5. Server-Side Logic dengan Side Effect

- `[BSL-005]` `[MATCH]` `sale.report` mendapat 3 kolom lewat `_select_additional_fields()`: `amount_received`, `waiting_for_payment`, `amount_to_invoice` (sumber `l.asa_amount_to_invoice`) — masing-masing `CASE WHEN l.product_id IS NOT NULL THEN SUM(l.<kolom>) ELSE 0 END`. Tidak dikalikan kurs.
  **Lokasi:** `advanced_sales_analysis/models/sale_report.py:6-18`
- `[BSL-006]` `[MATCH]` `account.move._compute_amount_paid`: `out_refund` + `payment_state in ('paid','in_payment','partial')` → `amount_paid_cn = amount_total - amount_residual`; `out_invoice` kondisi sama → `amount_paid = amount_total - amount_residual`. Tanpa cabang `else`. Kolisi nama field+method dengan `account_payment` — modul menang di MRO.
  **Lokasi:** `sale_report.py:22-41`
- `[BSL-007]` `[MATCH]` `account.move._compute_amount_dp` mengisi 6 field, reset `0.0` tiap record; assignment `=` di dalam loop → baris DP terakhir yang menang.
  **Lokasi:** `sale_report.py:43-83`
- `[BSL-008]` `[MATCH]` `sale.order.line._compute_asa_amount_to_invoice`: baris `state in ('sale','done')` → hitung `price_subtotal` lokal (invoice_policy, pajak `price_include` via `tax_ids.compute_all`). Cabang normal TETAP memakai field `line.price_subtotal` (dead-code path, dipertahankan). Cabang diskon-beda memakai `_convert` per baris faktur.
  **Lokasi:** `sale_report.py:86-143`
- `[BSL-009]` `[MATCH]` `_compute_waiting_for_payment_research`: iterasi baris faktur `state != 'cancel'` dan `payment_state in ('not_paid','partial')`, akumulasi `fixed_waiting_for_payment` + gross-up `dp_proportion` kalau ada baris DP (search `account.move.line` `product_id.name ilike 'Down payment'`).
  **Lokasi:** `sale_report.py:145-192`
- `[BSL-010]` `[MATCH]` `_compute_amount_received_research`: pola simetris, `payment_state in ('paid','in_payment','partial')`, pakai `move.amount_paid`/`amount_paid_cn`.
  **Lokasi:** `sale_report.py:194-238`
- `[BSL-011]` `[MATCH]` Perlakuan `payment_state == 'partial'` tidak konsisten antar method (`_compute_amount_dp` tidak menghitung `partial` sebagai dibayar).
- `[BSL-012]` `[MATCH]` Historis — tidak ada override `_group_by_sale()` (lihat `[BSL-023]`).

## 6. Client-Side Behavior

**N/A.** Tidak ada view/XML, controller aktif, asset/JS/Owl. Ketiga field `sale.report` muncul otomatis sebagai *Measures* di pivot/graph Sales Analysis (diverifikasi browser headless di 19.0: `test_qa_browser.py`).

## 7. Dependency Eksternal

- Manifest: `base`, `sale`, `account`, `sale_management` — Native Community.
- Implisit: `account_payment` (kolisi `[BSL-006]`); `point_of_sale`/`pos_sale` kalau terinstall (UNION `sale.report`; di 19.0 baris POS mendapat `NULL` untuk 3 kolom modul lewat `_fill_pos_fields()`).
- Instance produksi dev: Odoo Enterprise (modul tidak depend Enterprise).

## 8. Quirk / Behavior Non-Obvious

- `[BSL-013]` `[MATCH]` Deteksi uang muka lewat nama produk literal `"Down payment"` (9 tempat), bukan `is_downpayment`.
- `[BSL-014]` `[MATCH]` 3 kolom `sale.report` tidak dikonversi mata uang (kolom core dikonversi).
- `[BSL-015]` `[MATCH]` `security/ir.model.access.csv` ada tapi tidak dimuat (di-comment di manifest), merujuk model yang tidak ada.
- `[BSL-016]` `[MATCH]` `controllers/controllers.py` kosong tapi di-import.
- `[BSL-017]` `[MATCH]` Label duplikat/salah: 4 field `account.move` `'amount dp'`, 2 `'amount refund'`; `asa_amount_to_invoice` berlabel `'Amount Received'`. WARNING "same label" saat install.
- `[BSL-018]` `[MATCH]` File verifikasi Google Search Console (`googleaeed8a7b9ec156e7.html`) di folder addon & root repo.
- `[BSL-019]` `[MATCH]` `search()` `account.move.line` di dalam loop bersarang (2 method).
- `[BSL-020]` `[MATCH]` Faktur `amount_untaxed == 0` berkontribusi 0.
- `[BSL-021]` `[MATCH]` `@api.depends` melingkar antar 3 field `sale.order.line`.
- `[BSL-022]` `[MATCH]` Manifest tanpa key `assets`.
- `[BSL-023]` `[MATCH]` State baseline: (1) 3 kolom lewat hook resmi (bukan override `_select_sale`/`_group_by_sale`); (2) granularitas GROUP BY = core versi berjalan (19.0: `l.product_id, l.order_id, l.price_unit, l.invoice_status, t.uom_id, …, l.is_downpayment, l.discount, s.id, account_currency_table.rate`); test `test_ac_07_03_group_by_granularitas_18_0` → 2 baris untuk 2 baris SO produk sama harga beda; (3) field `asa_amount_to_invoice` (rename MF-02 17→18) permanen.
- `[BSL-024]` `[MATCH]` (ref: MF-01 18→19) `_compute_asa_amount_to_invoice` membaca `line.tax_ids` / `l.tax_ids` (bukan `tax_id`). Diverifikasi `test_ac_06_03b_tax_ids_rename_price_include`.

---

## Cara Pakai

1. Rekonsiliasi 1:1 dari baseline 18.0 + MF-01 18→19, di-cross-check ke kode `migration/19.0`.
2. Input untuk `03_MIGRATION_SPEC.md` dan dasar `05a_MIGRATION_ACCEPTANCE_CRITERIA.md` (tiap AC menyebut `BSL-NNN`).
3. ID `BSL-NNN` tidak dipakai ulang untuk klaim lain di project 19→20.
