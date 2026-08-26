# Migration Acceptance Criteria — advanced_sales_analysis

**Step:** 5 — Acceptance Criteria & Test Plan
**Ref:** `01_intake/01b_BASELINE_SPEC.md` dan kode 18.0 yang berjalan — **bukan** `03_spec/03_MIGRATION_SPEC.md`
**Tanggal:** 2026-08-26

> Format Given/When/Then, diturunkan dari `01b_BASELINE_SPEC.md`. **Then** menuliskan perilaku yang
> harus IDENTIK antara 18.0 (baseline) dan 19.0 (target) — kesetaraan diukur terhadap 18.0, bukan
> terhadap rencana migrasi. Sumber Given/When/Then diadaptasi 1:1 dari
> `doc-dev/migration_17.0_18.0/doc/05_acceptance/05a_MIGRATION_ACCEPTANCE_CRITERIA.md` (AC 17→18,
> execution-verified 38/38 test) — field yang di-rename saat migrasi sebelumnya (`amount_to_invoice`→
> `asa_amount_to_invoice`, MF-02) sudah disesuaikan namanya di sini.

---

## AC-01 — Instalasi & registrasi field (verifies `[BSL-005]`)

**AC-01-01**
Given database Odoo 19.0 dengan `sale`, `account`, `sale_management` terinstall
When modul `advanced_sales_analysis` diinstall
Then instalasi selesai tanpa error, dan kolom `amount_received`, `amount_to_invoice`, `waiting_for_payment` ada di SQL view `sale_report` — identik 18.0.

**AC-01-02**
Given modul terinstall di 19.0
When user membuka Sales → Reporting → Sales Analysis dan membuka dropdown *Measures*
Then ketiga measure baru muncul di daftar — identik 18.0.

---

## AC-02 — Kolisi `amount_paid` dengan `account_payment` (verifies `[BSL-006]`)

**AC-02-01**
Given `account_payment` ikut terinstall (auto_install pada `account`)
When registry Odoo 19.0 dibangun
Then `account.move.amount_paid` hanya punya SATU definisi efektif — definisi modul ini menang, tanpa error/warning saat instalasi (`02_DIFF_ANALYSIS.md` DIFF-04 mengkonfirmasi definisi core `account_payment` byte-identik 18.0↔19.0, jadi karakter kolisi ini harus identik, bukan berubah).

**AC-02-02**
Given customer invoice (`out_invoice`) bernilai 100 yang sudah dibayar penuh
When `amount_paid` dibaca
Then `amount_paid == 100` (`amount_total − amount_residual`) — identik 18.0.

**AC-02-03**
Given credit note (`out_refund`) bernilai 40 yang sudah dibayar
When `amount_paid_cn` dibaca
Then `amount_paid_cn == 40` — identik 18.0.

**AC-02-04**
Given jurnal umum (`move_type == 'entry'`) atau vendor bill (`in_invoice`), ATAU customer invoice ber-`payment_state == 'not_paid'`
When record dibuat/disimpan
Then `amount_paid`/`amount_paid_cn` tersimpan `NULL` (dibaca `0.0` dari Python), tanpa error — identik 18.0.

---

## AC-03 — Komponen uang muka `account.move` (verifies `[BSL-007]`, `[BSL-011]`, `[BSL-013]`)

**AC-03-01**
Given customer invoice ber-baris produk `"Down payment"` (`price_subtotal` positif), belum dibayar
When `amount_dp2_nopaid` dibaca
Then `amount_dp2_nopaid == price_subtotal` baris itu, `amount_dp2 == 0` — identik 18.0.

**AC-03-02**
Given satu faktur dengan DUA baris produk `"Down payment"` positif (dua termin DP)
When `amount_dp2` dibaca
Then nilainya HANYA dari baris terakhir yang diiterasi (bukan penjumlahan keduanya) — bug dipertahankan identik, BUKAN diperbaiki jadi akumulasi.

**AC-03-03**
Given faktur uang muka yang terbayar SEBAGIAN (`payment_state == 'partial'`)
When `amount_dp2`/`amount_dp2_nopaid` dibaca
Then seluruh nilai masuk `amount_dp2_nopaid` (dianggap 100% belum dibayar), `amount_dp2 == 0` — inkonsistensi dipertahankan identik.

**AC-03-04**
Given database berbahasa non-Inggris (produk DP bernama `"Acompte"`/`"Uang Muka"`, bukan literal `"Down payment"`)
When faktur uang muka dibuat
Then TIDAK ada baris yang dikenali sebagai DP — keenam field `amount_dp*` tetap `0.0` — deteksi tetap by hardcoded string, dipertahankan identik.

---

## AC-04 — `sale.order.line.amount_received` (verifies `[BSL-010]`, `[BSL-020]`)

**AC-04-01**
Given SO terkonfirmasi 100 (satu baris, tanpa pajak/DP), difakturkan penuh dan dibayar lunas
When `amount_received` dibaca
Then `amount_received == 100` — identik 18.0.

**AC-04-02**
Given faktur 100 dibayar 60 (`partial`)
When `amount_received` dibaca
Then `amount_received == 60` (`amount_paid × (100/100)`) — identik 18.0.

**AC-04-03**
Given credit note terbayar yang menghapus 40 dari nilai yang sudah diterima
When `amount_received` dibaca
Then nilainya berkurang 40 — identik 18.0.

**AC-04-04**
Given faktur ber-`amount_untaxed == 0` (mis. 100% diskon) berstatus dibayar
When `amount_received` dibaca
Then kontribusi baris itu 0 (guard bagi-nol) — identik 18.0.

---

## AC-05 — `sale.order.line.waiting_for_payment` (verifies `[BSL-009]`)

**AC-05-01**
Given SO 100 sudah difakturkan penuh, faktur di-post tapi belum dibayar
When `waiting_for_payment` dibaca
Then `waiting_for_payment == 100` — identik 18.0.

**AC-05-02**
Given faktur 100 dibayar 60 (`partial`)
When `waiting_for_payment` dibaca
Then `waiting_for_payment == 40` — identik 18.0.

**AC-05-03**
Given satu baris SO dengan DUA faktur berbeda (faktur A lunas, faktur B belum dibayar)
When `waiting_for_payment` dibaca
Then hasilnya BENAR mencerminkan sisa faktur B yang belum dibayar — identik 18.0.

---

## AC-06 — `sale.order.line.asa_amount_to_invoice` (verifies `[BSL-008]`, `[BSL-021]`) — **field ini bergantung LANGSUNG ke fix DIFF-01**

> **Semua AC di grup ini menjalankan `_compute_asa_amount_to_invoice()`, method yang berisi 2 pemanggilan `line.tax_id` yang WAJIB sudah di-rename `line.tax_ids` (DIFF-01, `03_MIGRATION_SPEC.md` Critical Blocker #2) sebelum test-test ini bisa lulus di 19.0.** Kalau fix belum diterapkan, seluruh AC-06 gagal dengan `AttributeError`, bukan assertion mismatch — bedakan dua jenis kegagalan ini di Step 9.

**AC-06-01**
Given SO 100 terkonfirmasi belum difakturkan sama sekali
When `asa_amount_to_invoice` dibaca
Then `asa_amount_to_invoice == 100` — identik 18.0.

**AC-06-02**
Given SO 100 sudah difakturkan penuh dan dibayar lunas
When `asa_amount_to_invoice` dibaca
Then `asa_amount_to_invoice == 0` — identik 18.0.

**AC-06-03** — **AC paling kritis di seluruh modul (warisan F-17/dead-code path, dipertahankan)**
Given baris SO ber-`invoice_policy == 'delivery'` dengan `product_uom_qty = 10` tapi `qty_delivered = 4` (harga satuan 10, tanpa diskon/pajak `price_include`)
When `asa_amount_to_invoice` dihitung
Then hasilnya **`100.0`, BUKAN `40.0`** — dead-code path (cabang normal memakai FIELD `line.price_subtotal`, mengabaikan `invoice_policy`) dipertahankan identik 18.0→19.0. `02_DIFF_ANALYSIS.md` DIFF-01/DIFF-03 mengkonfirmasi tidak ada perubahan core yang mempengaruhi logic ini (cuma rename accessor `tax_id`→`tax_ids` yang dipakai di CABANG LAIN method yang sama — pajak `price_include`, tidak dilalui skenario AC ini karena tanpa pajak). **Kalau hasil test di 19.0 ternyata `40.0` — itu REGRESI yang harus dieskalasi**, bukan perbaikan yang menguntungkan (mengubah scope migrasi).

**AC-06-03b** (BARU untuk migrasi 18→19, menguji jalur pajak `price_include` yang menyentuh langsung DIFF-01)
Given baris SO dengan pajak `price_include=True` terpasang (`tax_id`/`tax_ids` diisi minimal 1 pajak inclusive), ber-diskon berbeda dari faktur (memaksa jalur `inv_lines.mapped(...)` di `_compute_asa_amount_to_invoice`, baris yang memanggil `.tax_id.compute_all()`/`.filtered()`)
When `asa_amount_to_invoice` dihitung
Then compute BERHASIL tanpa `AttributeError`, dan hasil numerik identik dengan hasil yang didapat di 18.0 untuk skenario input yang sama — ini AC yang secara eksplisit memverifikasi fix DIFF-01 (`line.tax_id`→`line.tax_ids`) berfungsi, bukan cuma "tidak crash" tapi juga "angka tetap benar".

**AC-06-04**
Given ketiga field (`asa_amount_to_invoice`/`waiting_for_payment`/`amount_received`) saling `@api.depends`
When salah satu berubah dan dibaca ulang dalam urutan berbeda (dengan `invalidate_recordset()` di antaranya)
Then hasilnya IDENTIK terlepas urutan pembacaan — dikonfirmasi TIDAK bermasalah lewat eksekusi migrasi 17→18 sebelumnya (`test_ac_06_05_urutan_pembacaan_field_melingkar`), tidak ada perubahan core 19.0 yang mempengaruhi ini (`02_DIFF_ANALYSIS.md` DIFF-03/DIFF-06). Tetap WAJIB di-re-run di Step 9 terhadap instance 19.0 sungguhan, bukan diasumsikan dari dokumen ini saja.

---

## AC-07 — `sale.report` (SQL view) (verifies `[BSL-005]`, `[BSL-014]`, `[BSL-023]`)

**AC-07-01**
Given satu SO terkonfirmasi dengan `amount_received = 100` di baris SO-nya
When `sale.report` di-`search_read` untuk order itu (setelah `self.env.flush_all()`)
Then `amount_received` di hasil laporan `== 100` — identik 18.0.

**AC-07-02**
Given baris `sale.report` yang `product_id`-nya NULL (baris section/note)
When kolom baru dibaca
Then bernilai 0 (guard `CASE WHEN l.product_id IS NOT NULL`) — identik 18.0.

**AC-07-03** — **granularitas GROUP BY dikonfirmasi STABIL 18.0→19.0 (beda dari migrasi 17→18 yang punya MF-01)**
Given satu SO dengan DUA baris produk SAMA, diskon SAMA, tapi `price_unit` BERBEDA (mis. 60.0 dan 40.0)
When `sale.report` dibaca
Then kedua baris **TERPECAH jadi 2 row** — sama seperti baseline 18.0 (bukan lagi berbeda antar versi seperti kasus 17.0 vs 18.0). `02_DIFF_ANALYSIS.md` DIFF-02 mengkonfirmasi `_group_by_sale()` byte-identik 18.0↔19.0 (28 kolom GROUP BY sama, termasuk `l.price_unit` yang jadi bagian baseline sejak MF-01). Test `test_ac_07_03_group_by_granularitas_18_0` (nama diwarisi apa adanya dari migrasi sebelumnya, assertion `len(rows) == 2`) diharapkan TETAP lulus tanpa perubahan assertion.

**AC-07-04**
Given SO dalam mata uang BERBEDA dari mata uang perusahaan
When `sale.report` dibaca
Then `price_subtotal` (core) sudah dikonversi ke mata uang perusahaan tapi `amount_received`/`waiting_for_payment`/`amount_to_invoice` TIDAK (dipertahankan identik) — angka di baris yang sama tidak sebanding, sama seperti 18.0. Catatan: mekanisme `currency_id` internal `sale.report` berubah (compute→literal SQL, `02_DIFF_ANALYSIS.md` §1 catatan informasional) tapi TIDAK disentuh/di-override modul ini — tidak mempengaruhi AC ini.

**AC-07-05** — **gap testing warisan, MASIH belum tertutup di migrasi ini juga**
Given `_select_additional_fields()` adalah hook yang SAMA dipakai `_select_pos()` milik `pos_sale` (tidak diinstall di test 17.0/18.0 sebelumnya)
When `sale.report._query()` dibangun di lingkungan 19.0 yang JUGA menginstall `point_of_sale`/`pos_sale`
Then UNION dua cabang tetap sinkron jumlah kolomnya. `02_DIFF_ANALYSIS.md` DIFF-05 mengkonfirmasi analisis STATIS (baca kode `_select_pos()` langsung) bahwa column count tetap matched simetris 18.0→19.0 (basis 39→40 kolom, tumbuh bersamaan) — **TAPI ini analisis statis, BUKAN eksekusi nyata dengan POS terinstall**, sama seperti gap yang sudah dicatat sejak migrasi 17→18. Tetap dicatat eksplisit sebagai gap testing yang belum tertutup, bukan diasumsikan aman.

---

## Ringkasan Traceability

30 AC (`AC-01-01` s/d `AC-07-05`, termasuk 1 AC baru `AC-06-03b` khusus memverifikasi fix DIFF-01), mencakup 12 dari 23 `BSL-NNN` di `01b_BASELINE_SPEC.md` — sisanya (`[BSL-001]`-`[BSL-004]` user stories umum, `[BSL-012]` historis/tidak berlaku, item structural/scaffold `[BSL-015]`/`[BSL-016]`/`[BSL-017]`/`[BSL-018]`/`[BSL-019]`/`[BSL-022]`) sengaja tidak diberi AC eksekutif — sama seperti keputusan migrasi 17→18 sebelumnya.

**2 AC bertanda eksplisit "belum dikonfirmasi eksekusi langsung terhadap 19.0"**: AC-06-04 (urutan `@api.depends`), AC-07-05 (UNION dengan POS terinstall) — WAJIB mendapat hasil test nyata di `05b_TEST_PLAN_MIGRATION.md`/Step 9, tidak boleh ditutup hanya dengan analisis dokumen.

**1 AC BARU (`AC-06-03b`) wajib lulus sebagai bukti fix DIFF-01 bekerja** — ini bukan cuma "regression tetap lulus", tapi verifikasi POSITIF bahwa perubahan kode (rename `tax_id`→`tax_ids`) benar dan tidak mengubah hasil numerik.
