# Migration Acceptance Criteria — advanced_sales_analysis

**Step:** 5 — Acceptance Criteria & Test Plan
**Ref:** `01_intake/01b_BASELINE_SPEC.md` dan kode 17.0 yang berjalan — **bukan** `03_spec/03_MIGRATION_SPEC.md`
**Tanggal:** 2026-08-21

> Format Given/When/Then, diturunkan dari `01b_BASELINE_SPEC.md`. **Then** menuliskan perilaku yang
> harus IDENTIK antara 17.0 (baseline) dan 18.0 (target) — kesetaraan diukur terhadap 17.0, bukan
> terhadap rencana migrasi. Sumber Given/When/Then diadaptasi dari
> `doc-dev/backfill/spec/01B_ACCEPTANCE_CRITERIA.md` (AC lama, execution-verified 17.0) — beberapa
> teks **dikoreksi** di sini mengikuti hasil eksekusi nyata Step 04 backfill (dicatat di `FINDINGS.md`),
> BUKAN asumsi awal Step 01 backfill yang sudah terbukti salah (lihat catatan koreksi per AC).

---

## AC-01 — Instalasi & registrasi field (verifies `[BSL-005]`)

**AC-01-01**
Given database Odoo 18.0 dengan `sale`, `account`, `sale_management` terinstall
When modul `advanced_sales_analysis` diinstall
Then instalasi selesai tanpa error, dan kolom `amount_received`, `amount_to_invoice`, `waiting_for_payment` ada di SQL view `sale_report` — identik 17.0.

**AC-01-02**
Given modul terinstall di 18.0
When user membuka Sales → Reporting → Sales Analysis dan membuka dropdown *Measures*
Then ketiga measure baru muncul di daftar — identik 17.0.

---

## AC-02 — Kolisi `amount_paid` dengan `account_payment` (verifies `[BSL-006]`)

**AC-02-01**
Given `account_payment` ikut terinstall (auto_install pada `account`)
When registry Odoo 18.0 dibangun
Then `account.move.amount_paid` hanya punya SATU definisi efektif — definisi modul ini menang (dikonfirmasi eksekusi backfill 17.0; `02_DIFF_ANALYSIS.md` DIFF-02 mengkonfirmasi definisi core `account_payment` byte-identik 17.0↔18.0, jadi karakter kolisi ini harus identik, bukan berubah) — tanpa error/warning saat instalasi.

**AC-02-02**
Given customer invoice (`out_invoice`) bernilai 100 yang sudah dibayar penuh
When `amount_paid` dibaca
Then `amount_paid == 100` (`amount_total − amount_residual`) — identik 17.0.

**AC-02-03**
Given credit note (`out_refund`) bernilai 40 yang sudah dibayar
When `amount_paid_cn` dibaca
Then `amount_paid_cn == 40` — identik 17.0.

**AC-02-04** — **koreksi dari asumsi awal Step 01 backfill**
Given jurnal umum (`move_type == 'entry'`) atau vendor bill (`in_invoice`), ATAU customer invoice ber-`payment_state == 'not_paid'`
When record dibuat/disimpan
Then `amount_paid`/`amount_paid_cn` tersimpan `NULL` (dibaca `0.0` dari Python) — **BUKAN error compute-tidak-assign** (dugaan awal Step 01 backfill terbukti salah lewat eksekusi nyata: instalasi dengan 24 demo `account.move` berhasil bersih, 0/24 ter-assign, tanpa traceback). Perilaku ini harus identik di 18.0.

---

## AC-03 — Komponen uang muka `account.move` (verifies `[BSL-007]`, `[BSL-011]`, `[BSL-013]`)

**AC-03-01**
Given customer invoice ber-baris produk `"Down payment"` (`price_subtotal` positif), belum dibayar
When `amount_dp2_nopaid` dibaca
Then `amount_dp2_nopaid == price_subtotal` baris itu, `amount_dp2 == 0` — identik 17.0.

**AC-03-02**
Given satu faktur dengan DUA baris produk `"Down payment"` positif (dua termin DP)
When `amount_dp2` dibaca
Then nilainya HANYA dari baris terakhir yang diiterasi (bukan penjumlahan keduanya) — bug F-10 dipertahankan identik, BUKAN diperbaiki jadi akumulasi.

**AC-03-03**
Given faktur uang muka yang terbayar SEBAGIAN (`payment_state == 'partial'`)
When `amount_dp2`/`amount_dp2_nopaid` dibaca
Then seluruh nilai masuk `amount_dp2_nopaid` (dianggap 100% belum dibayar), `amount_dp2 == 0` — inkonsistensi F-11 dipertahankan identik (beda dari `_compute_amount_paid`/`_compute_waiting_for_payment_research`/`_compute_amount_received_research` yang MENGHITUNG `partial`).

**AC-03-04**
Given database berbahasa non-Inggris (produk DP bernama `"Acompte"`/`"Uang Muka"`, bukan literal `"Down payment"`)
When faktur uang muka dibuat
Then TIDAK ada baris yang dikenali sebagai DP — keenam field `amount_dp*` tetap `0.0` — bug F-04 dipertahankan identik (deteksi tetap by hardcoded string, `is_downpayment` resmi TIDAK dipakai walau tersedia stabil di 18.0 — `02_DIFF_ANALYSIS.md` DIFF-04).

---

## AC-04 — `sale.order.line.amount_received` (verifies `[BSL-010]`, `[BSL-020]`)

**AC-04-01**
Given SO terkonfirmasi 100 (satu baris, tanpa pajak/DP), difakturkan penuh dan dibayar lunas
When `amount_received` dibaca
Then `amount_received == 100` — identik 17.0.

**AC-04-02**
Given faktur 100 dibayar 60 (`partial`)
When `amount_received` dibaca
Then `amount_received == 60` (`amount_paid × (100/100)`) — identik 17.0.

**AC-04-03**
Given credit note terbayar yang menghapus 40 dari nilai yang sudah diterima
When `amount_received` dibaca
Then nilainya berkurang 40 — identik 17.0.

**AC-04-04**
Given faktur ber-`amount_untaxed == 0` (mis. 100% diskon) berstatus dibayar
When `amount_received` dibaca
Then kontribusi baris itu 0 (guard bagi-nol, F-16 dipertahankan) — identik 17.0.

---

## AC-05 — `sale.order.line.waiting_for_payment` (verifies `[BSL-009]`)

**AC-05-01**
Given SO 100 sudah difakturkan penuh, faktur di-post tapi belum dibayar
When `waiting_for_payment` dibaca
Then `waiting_for_payment == 100` — identik 17.0.

**AC-05-02**
Given faktur 100 dibayar 60 (`partial`)
When `waiting_for_payment` dibaca
Then `waiting_for_payment == 40` — identik 17.0.

**AC-05-03** — **koreksi dari asumsi awal Step 01 backfill**
Given satu baris SO dengan DUA faktur berbeda (faktur A lunas, faktur B belum dibayar)
When `waiting_for_payment` dibaca
Then hasilnya **BENAR** mencerminkan sisa faktur B yang belum dibayar (bukan dipaksa 0 seperti dugaan awal F-09 — terbukti salah lewat eksekusi: filter loop menjamin baris yang lolos selalu `amount_residual != 0`, jadi guard tidak pernah salah aktif pada kasus ini). Perilaku (termasuk kode yang secara struktural "menyesatkan" tapi tidak berdampak) harus identik di 18.0.

---

## AC-06 — `sale.order.line.amount_to_invoice` (verifies `[BSL-008]`, `[BSL-021]`)

**AC-06-01**
Given SO 100 terkonfirmasi belum difakturkan sama sekali
When `amount_to_invoice` dibaca
Then `amount_to_invoice == 100` — identik 17.0.

**AC-06-02**
Given SO 100 sudah difakturkan penuh dan dibayar lunas
When `amount_to_invoice` dibaca
Then `amount_to_invoice == 0` — identik 17.0.

**AC-06-03** — **koreksi dari asumsi awal Step 01 backfill (ini AC PALING KRITIS di seluruh modul)**
Given baris SO ber-`invoice_policy == 'delivery'` dengan `product_uom_qty = 10` tapi `qty_delivered = 4` (harga satuan 10, tanpa diskon/pajak `price_include`)
When `amount_to_invoice` dihitung
Then hasilnya **`100.0`, BUKAN `40.0`** — dugaan awal Step 01 ("basis pakai `qty_delivered`") terbukti SALAH lewat eksekusi nyata (F-17, `test_ac_06_04_invoice_policy_delivery_diabaikan`): cabang normal memakai FIELD `line.price_subtotal` (mengabaikan `invoice_policy`/pajak `price_include` sepenuhnya), bukan variabel lokal yang sudah dihitung benar. **Bug ini WAJIB terbawa identik ke 18.0** — `02_DIFF_ANALYSIS.md` DIFF-03 mengkonfirmasi core `_compute_untaxed_amount_to_invoice()` (referensi yang seharusnya diikuti) byte-identik 17.0↔18.0, jadi tidak ada "perbaikan gratis" dari sisi core. **Kalau hasil test di 18.0 ternyata `40.0` (bukan `100.0`) — itu REGRESI yang harus dieskalasi, bukan dianggap perbaikan yang menguntungkan**, karena mengubah scope migrasi ini.

**AC-06-04** — **koreksi dari asumsi awal Step 01 backfill**
Given ketiga field (`amount_to_invoice`/`waiting_for_payment`/`amount_received`) saling `@api.depends`
When salah satu berubah dan dibaca ulang dalam urutan berbeda (dengan `invalidate_recordset()` di antaranya)
Then hasilnya **IDENTIK terlepas urutan pembacaan** — dugaan awal Step 01 ("bergantung urutan evaluasi, tidak deterministik") terbukti SALAH lewat eksekusi (F-03, `test_ac_06_05_urutan_pembacaan_field_melingkar`). **Item ini statusnya "kemungkinan sama" untuk 18.0, BELUM dikonfirmasi eksekusi langsung** (`02_DIFF_ANALYSIS.md` DIFF-06) — test yang sama WAJIB di-re-run terhadap instance 18.0 sungguhan di Step 9, hasil `[MATCH]`/tidak dicatat eksplisit di sana, bukan diasumsikan dari dokumen ini saja.

---

## AC-07 — `sale.report` (SQL view) (verifies `[BSL-005]`, `[BSL-014]`, `[BSL-023]`)

**AC-07-01**
Given satu SO terkonfirmasi dengan `amount_received = 100` di baris SO-nya
When `sale.report` di-`search_read` untuk order itu (setelah `self.env.flush_all()` — SQL view membaca tabel dasar langsung, bypass cache ORM)
Then `amount_received` di hasil laporan `== 100` — identik 17.0.

**AC-07-02**
Given baris `sale.report` yang `product_id`-nya NULL (baris section/note)
When kolom baru dibaca
Then bernilai 0 (guard `CASE WHEN l.product_id IS NOT NULL`) — identik 17.0.

**AC-07-03** — **koreksi 2026-08-21 setelah eksekusi G1 (MF-01, `FINDINGS.md`) — beda antara 17.0 dan 18.0, disengaja & disetujui**
Given satu SO dengan DUA baris produk SAMA, diskon SAMA, tapi `price_unit` BERBEDA (mis. 60.0 dan 40.0)
When `sale.report` dibaca
Then perilaku **BERBEDA antar versi, keduanya benar untuk versinya masing-masing:**
- **Di 17.0:** kedua baris MENYATU jadi 1 row (`price_unit` bukan bagian GROUP BY core 17.0) — hasil fix F-19/F-06.
- **Di 18.0:** kedua baris TERPECAH jadi 2 row — core `_group_by_sale()` 18.0 menambah `l.price_unit` (juga `l.invoice_status`, `l.is_downpayment`) ke GROUP BY, independen dari modul ini (modul tidak override method itu).

**Ini BUKAN regresi** — dikonfirmasi eksekusi (`test_ac_07_03_group_by_granularitas_18_0`), root cause di core Odoo, disetujui pemilik modul sebagai penyimpangan yang diterima (Opsi 1, MF-01) alih-alih dipaksa identik lewat override manual (berisiko menghidupkan pola bug F-19). **Baseline 18.0 yang benar: 2 row untuk skenario ini**, bukan 1.

**AC-07-04**
Given SO dalam mata uang BERBEDA dari mata uang perusahaan
When `sale.report` dibaca
Then `price_subtotal` (core) sudah dikonversi ke mata uang perusahaan tapi `amount_received`/`waiting_for_payment`/`amount_to_invoice` TIDAK (F-05 dipertahankan identik) — angka di baris yang sama tidak sebanding, sama seperti 17.0.

**AC-07-05** (baru, spesifik konteks migrasi — tidak ada di AC backfill 17.0)
Given `_select_additional_fields()` (`[BSL-005]`) adalah hook yang SAMA dipakai `_select_pos()` milik `point_of_sale` (Community, tidak diinstall di test 17.0 backfill)
When `sale.report._query()` dibangun di lingkungan 18.0 yang JUGA menginstall `point_of_sale`
Then UNION dua cabang (`_select_sale()` dan `_select_pos()`) tetap sinkron jumlah kolomnya (tidak terulang error F-19) — **belum pernah dites langsung dengan POS terinstall bersamaan di versi manapun (17.0 maupun 18.0)**, dicatat eksplisit sebagai gap testing, bukan diasumsikan aman hanya dari desain hook resmi.

---

## Ringkasan Traceability

29 AC (`AC-01-01` s/d `AC-07-05`), mencakup 12 dari 23 `BSL-NNN` di `01b_BASELINE_SPEC.md` — sisanya (`[BSL-001]`-`[BSL-004]` user stories umum, `[BSL-012]` historis/tidak berlaku, `[BSL-015]`/`[BSL-016]`/`[BSL-017]`/`[BSL-018]`/`[BSL-019]`/`[BSL-022]` structural/scaffold tanpa dampak fungsional yang bisa diuji Given/When/Then bermakna) sengaja tidak diberi AC eksekutif — dicatat cukup sebagai bagian `01b_BASELINE_SPEC.md` untuk kesadaran code review (Step 8), bukan test case. Kalau reviewer Step 8 menganggap salah satu di antaranya perlu AC eksplisit, itu bisa ditambahkan susulan di sini.

**3 AC bertanda eksplisit "belum dikonfirmasi eksekusi langsung terhadap 18.0"** (AC-06-04/DIFF-06, AC-07-05) — WAJIB mendapat hasil test nyata di `05b_TEST_PLAN_MIGRATION.md`/Step 9, tidak boleh ditutup hanya dengan analisis dokumen.
