# Acceptance Criteria — advanced_sales_analysis

**Module:** `advanced_sales_analysis`
**Ref:** `01A_FUNCTIONAL_SPEC.md`
**Last Updated:** 2026-08-18
**Status:** Backfill retroaktif

> Given/When/Then diturunkan dari Business Rules di `01A_FUNCTIONAL_SPEC.md`. **Then** menuliskan
> apa yang SEKARANG terjadi di kode — bukan apa yang seharusnya terjadi. AC ber-tag
> `[PERLU-KEPUTUSAN]` artinya perilaku sekarang kemungkinan bukan yang diinginkan; lihat
> `FINDINGS.md`.

---

## AC-01 — Instalasi & registrasi field

**AC-01-01** — ref `BR-01` `[HASIL-BACA]`
Given database Odoo 17.0 dengan `sale`, `account`, `sale_management` terinstall
When modul `advanced_sales_analysis` diinstall
Then instalasi selesai tanpa error, dan kolom `amount_received`, `amount_to_invoice`,
`waiting_for_payment` ada di SQL view `sale_report`

**AC-01-02** — ref `BR-01` `[HASIL-BACA]`
Given modul terinstall
When user membuka Sales → Reporting → Sales Analysis dan membuka dropdown *Measures*
Then ketiga measure baru muncul di daftar (otomatis, karena field numerik tanpa view kustom)

**AC-01-03** — ref `BR-06` `[PERLU-KEPUTUSAN]` → F-01
Given `account_payment` ikut terinstall (auto_install pada `account` — kondisi normal)
When registry Odoo dibangun
Then `account.move.amount_paid` hanya punya SATU definisi efektif dan SATU method
`_compute_amount_paid` yang menang — yang mana bergantung urutan load modul, dan yang kalah
kehilangan seluruh semantiknya tanpa error/warning

---

## AC-02 — `account.move`: pemecahan nilai dibayar

**AC-02-01** — ref `BR-06` `[HASIL-BACA]`
Given customer invoice (`out_invoice`) bernilai 100 yang sudah dibayar penuh
When `amount_paid` dibaca
Then `amount_paid == 100` (`amount_total − amount_residual`)

**AC-02-02** — ref `BR-06` `[HASIL-BACA]`
Given credit note (`out_refund`) bernilai 40 yang sudah dibayar
When `amount_paid_cn` dibaca
Then `amount_paid_cn == 40`

**AC-02-03** — ref `BR-06` `[PERLU-KEPUTUSAN]` → F-02
Given jurnal umum (`move_type == 'entry'`) atau vendor bill (`in_invoice`) apa pun
When record dibuat/disimpan sehingga stored compute dijalankan
Then TIDAK ada nilai yang ditugaskan ke `amount_paid` maupun `amount_paid_cn` — Odoo
melempar error compute-tidak-assign (harus dibuktikan di Step 04)

**AC-02-04** — ref `BR-06` `[PERLU-KEPUTUSAN]` → F-02
Given customer invoice yang di-post tapi belum dibayar (`payment_state == 'not_paid'`)
When record disimpan
Then cabang `if` maupun `elif` tidak ada yang meng-assign → perilaku sama seperti AC-02-03

---

## AC-03 — `account.move`: komponen uang muka

**AC-03-01** — ref `BR-07` `[HASIL-BACA]`
Given customer invoice ber-baris produk `"Down payment"` dengan `price_subtotal` positif, belum
dibayar
When `amount_dp2_nopaid` dibaca
Then `amount_dp2_nopaid == price_subtotal` baris itu, dan `amount_dp2 == 0`

**AC-03-02** — ref `BR-07` `[HASIL-BACA]`
Given faktur final yang memotong uang muka (baris `"Down payment"` dengan `price_subtotal`
negatif), sudah dibayar
When `amount_dp` dibaca
Then `amount_dp == price_subtotal` (nilai negatif), dan `amount_dp_nopaid == 0`

**AC-03-03** — ref `BR-07` `[PERLU-KEPUTUSAN]` → F-10
Given satu faktur dengan DUA baris produk `"Down payment"` positif (mis. dua termin DP)
When `amount_dp2` dibaca
Then nilainya HANYA dari baris terakhir yang diiterasi — bukan penjumlahan keduanya

**AC-03-04** — ref `BR-07`, `BR-08` `[PERLU-KEPUTUSAN]` → F-11
Given faktur uang muka yang terbayar SEBAGIAN (`payment_state == 'partial'`)
When `amount_dp2` / `amount_dp2_nopaid` dibaca
Then seluruh nilai masuk ke `amount_dp2_nopaid` (dianggap belum dibayar sama sekali), `amount_dp2 == 0`

**AC-03-05** — ref `BR-07`, `BR-04` `[PERLU-KEPUTUSAN]` → F-04
Given database berbahasa non-Inggris (produk uang muka bernama mis. `"Acompte"` / `"Uang Muka"`)
When faktur uang muka dibuat
Then tidak ada baris yang dikenali sebagai DP — keenam field `amount_dp*` tetap `0.0` dan seluruh
logika gross-up DP di BR-04/BR-05 tidak pernah aktif

---

## AC-04 — `sale.order.line.amount_received`

**AC-04-01** — ref `BR-05` `[HASIL-BACA]`
Given SO terkonfirmasi bernilai 100 (satu baris, tanpa pajak, tanpa DP), difakturkan penuh dan
faktur dibayar lunas
When `amount_received` baris SO dibaca
Then `amount_received == 100`

**AC-04-02** — ref `BR-05` `[HASIL-BACA]`
Given SO terkonfirmasi yang sudah difakturkan tapi faktur belum dibayar sama sekali
When `amount_received` dibaca
Then `amount_received == 0` (tidak ada baris faktur yang lolos filter `payment_state`)

**AC-04-03** — ref `BR-05` `[HASIL-BACA]`
Given faktur 100 yang dibayar 60 (`payment_state == 'partial'`), satu baris SO
When `amount_received` dibaca
Then `amount_received == 60` — `amount_paid (60) × (100/100)`

**AC-04-04** — ref `BR-05` `[HASIL-BACA]`
Given faktur dengan DUA baris berbeda produk (masing-masing 60 dan 40) yang dibayar lunas
When `amount_received` masing-masing baris SO dibaca
Then terbagi proporsional: 60 dan 40

**AC-04-05** — ref `BR-05` `[HASIL-BACA]`
Given credit note terbayar yang menghapus 40 dari nilai yang sudah diterima
When `amount_received` dibaca
Then nilainya berkurang 40 (`amount_paid_cn × proporsi`)

**AC-04-06** — ref `BR-05` `[HASIL-BACA]`
Given baris SO produknya bernama `"Down payment"`
When `amount_received` dibaca
Then nilainya `amount_dp2 + amount_dp − amount_refund` terakumulasi, BUKAN hasil proporsional

**AC-04-07** — ref `BR-05` `[PERLU-KEPUTUSAN]` → F-16
Given faktur ber-`amount_untaxed == 0` (mis. 100% diskon) yang berstatus dibayar
When `amount_received` dibaca
Then kontribusi baris itu 0 (guard bagi-nol aktif) — nilai faktur tidak pernah tercermin

---

## AC-05 — `sale.order.line.waiting_for_payment`

**AC-05-01** — ref `BR-04` `[HASIL-BACA]`
Given SO 100 yang sudah difakturkan penuh, faktur di-post tapi belum dibayar
When `waiting_for_payment` dibaca
Then `waiting_for_payment == 100`

**AC-05-02** — ref `BR-04` `[HASIL-BACA]`
Given faktur 100 yang dibayar 60 (`partial`)
When `waiting_for_payment` dibaca
Then `waiting_for_payment == 40` (`amount_residual × proporsi`)

**AC-05-03** — ref `BR-04` `[HASIL-BACA]`
Given SO terkonfirmasi yang belum difakturkan sama sekali
When `waiting_for_payment` dibaca
Then `waiting_for_payment == 0` (tidak ada `_get_invoice_lines()`)

**AC-05-04** — ref `BR-04` `[HASIL-BACA]`
Given faktur yang di-cancel
When `waiting_for_payment` dibaca
Then baris faktur itu diabaikan (`state != 'cancel'`)

**AC-05-05** — ref `BR-04` `[PERLU-KEPUTUSAN]` → F-09
Given baris SO yang punya LEBIH DARI SATU baris faktur belum dibayar dari faktur BERBEDA
When `waiting_for_payment` dibaca
Then guard akhir (`amount_residual == 0`) hanya mengevaluasi `amount_residual` dari faktur
TERAKHIR yang diiterasi — bukan seluruhnya; hasil akhir bisa dipaksa jadi 0 walau masih ada
tagihan terbuka dari faktur lain

---

## AC-06 — `sale.order.line.amount_to_invoice`

**AC-06-01** — ref `BR-03` `[HASIL-BACA]`
Given SO 100 terkonfirmasi yang belum difakturkan sama sekali
When `amount_to_invoice` dibaca
Then `amount_to_invoice == 100` (`price_subtotal − (0 + 0)`)

**AC-06-02** — ref `BR-03` `[HASIL-BACA]`
Given SO 100 yang sudah difakturkan penuh dan dibayar lunas
When `amount_to_invoice` dibaca
Then `amount_to_invoice == 0` (`100 − (0 + 100)`)

**AC-06-03** — ref `BR-03` `[HASIL-BACA]`
Given SO masih draft (`state == 'draft'`)
When `amount_to_invoice` dibaca
Then `amount_to_invoice == 0`

**AC-06-04** — ref `BR-03` `[HASIL-BACA]`
Given baris SO ber-`invoice_policy == 'delivery'` dengan `product_uom_qty = 10` tapi
`qty_delivered = 4`
When `amount_to_invoice` dihitung
Then basis subtotal memakai `qty_delivered` (4), bukan `product_uom_qty`

**AC-06-05** — ref `BR-03` `[PERLU-KEPUTUSAN]` → F-03
Given ketiga field saling `@api.depends`
When salah satu dari `amount_received` / `waiting_for_payment` berubah
Then Odoo memicu rekomputasi berantai yang saling merujuk — hasil akhir bergantung urutan
evaluasi, bukan deterministik dari input

---

## AC-07 — `sale.report` (SQL view)

**AC-07-01** — ref `BR-01` `[HASIL-BACA]`
Given satu SO terkonfirmasi dengan `amount_received = 100` di baris SO-nya
When `sale.report` di-`search_read` untuk order itu
Then `amount_received` di hasil laporan `== 100`
**Catatan test:** butuh `self.env.flush_all()` sebelum query — `sale.report` adalah SQL view yang
membaca tabel dasar langsung, mem-bypass cache ORM (lihat
`doc-dev-backfill/records/advanced_sales_analysis/SUMMARY.md` CAND-03)

**AC-07-02** — ref `BR-01` `[HASIL-BACA]`
Given baris `sale.report` yang `product_id`-nya NULL (baris section/note)
When kolom baru dibaca
Then bernilai 0 (guard `CASE WHEN l.product_id IS NOT NULL`)

**AC-07-03** — ref `BR-02` `[PERLU-KEPUTUSAN]` → F-06
Given satu SO dengan DUA baris produk SAMA dan diskon SAMA tapi `amount_received` BERBEDA
When `sale.report` dibaca
Then kedua baris TIDAK menyatu jadi satu row (seperti perilaku core), melainkan terpecah — karena
ketiga kolom baru ikut masuk GROUP BY

**AC-07-04** — ref `BR-01` `[PERLU-KEPUTUSAN]` → F-05
Given SO dalam mata uang yang BERBEDA dari mata uang perusahaan
When `sale.report` dibaca
Then `price_subtotal` (core) sudah dikonversi ke mata uang perusahaan tapi `amount_received` /
`waiting_for_payment` / `amount_to_invoice` TIDAK — angka di baris yang sama jadi tidak
sebanding
