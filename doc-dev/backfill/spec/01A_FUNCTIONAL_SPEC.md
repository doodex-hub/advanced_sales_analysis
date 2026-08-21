# Functional Spec — advanced_sales_analysis

**Module:** `advanced_sales_analysis`
**Odoo Version:** 17.0
**Depends:** `base`, `sale`, `account`, `sale_management`
**Last Updated:** 2026-08-21 (backfill ulang — fix F-19 terintegrasi)
**Status:** Backfill retroaktif — dibaca dari kode existing, bukan requirement baru
**Provenance:** lihat `doc-dev-backfill/templates/CLAUDE_TEMPLATE.md` §Provenance Tag

---

## Ringkasan untuk Review — Perlu Konfirmasi User

> 6 poin paling kritis. Semuanya juga ada di `doc-dev/backfill/FINDINGS.md`.

1. **`amount_paid` + `_compute_amount_paid` di `account.move` BENTROK dengan modul core
   `account_payment`** (yang `auto_install: ['account']` — praktis SELALU ikut terinstall). Dua
   modul mendefinisikan field DAN method dengan nama PERSIS SAMA di model yang sama, dengan
   semantik yang benar-benar berbeda. Yang menang tergantung urutan load registry.
   `[PERLU-KEPUTUSAN]` → F-01
2. **`_compute_amount_paid` tidak menugaskan nilai di semua cabang** — untuk `move_type` selain
   `out_invoice`/`out_refund` (mis. `entry`, `in_invoice`), maupun `out_invoice` dengan
   `payment_state == 'not_paid'`, tidak satu pun dari `amount_paid`/`amount_paid_cn` di-assign.
   Field stored-compute yang tidak di-assign melempar error di Odoo. `[PERLU-KEPUTUSAN]` → F-02
3. **Dependency melingkar antar 3 stored compute di `sale.order.line`** — `amount_to_invoice`,
   `waiting_for_payment`, dan `amount_received` saling `@api.depends` satu sama lain.
   `[PERLU-KEPUTUSAN]` → F-03
4. **Deteksi baris uang muka lewat nama produk hardcoded `"Down payment"`** — pecah di database
   berbahasa non-Inggris atau kalau produk DP dinamai lain. `[PERLU-KEPUTUSAN]` → F-04
5. **Kolom baru di `sale.report` TIDAK dikonversi mata uang**, padahal semua kolom moneter core
   dibagi `s.currency_rate` dan dikali `currency_table.rate`.
   `[PERLU-KEPUTUSAN]` → F-05
6. ~~**`_group_by_sale()` menambah 3 kolom ke GROUP BY** — mengubah granularitas baris laporan.~~
   **✅ RESOLVED 2026-08-21** — fix F-19 menghapus override `_group_by_sale()` dan `_select_sale()`,
   diganti `_select_additional_fields()`. Granularitas laporan kembali identik dengan core. → F-06

---

## Latar Belakang & Tujuan

Modul memperkaya laporan **Sales Analysis** (`sale.report`) Odoo dengan tiga metrik finansial yang
tidak ada di core: **Amount Received** (uang yang benar-benar sudah diterima per baris penjualan),
**Waiting for Payment** (nilai yang sudah difakturkan tapi belum dibayar), dan **Amount To
Invoice** (sisa yang belum difakturkan sama sekali). `[HASIL-BACA]`

Karena `sale.report` adalah SQL view (`_auto=False`) yang membaca langsung tabel `sale_order_line`,
ketiga metrik itu tidak bisa dihitung di level laporan — modul menghitungnya lebih dulu sebagai
field **stored compute di `sale.order.line`**, lalu menariknya ke SQL view. Perhitungannya sendiri
bertumpu pada delapan field pembantu stored-compute di `account.move` yang memecah nilai faktur ke
komponen dibayar / belum dibayar / uang muka / retur. `[HASIL-BACA]`

Tujuan bisnis yang tersirat: menjawab "dari nilai order ini, berapa yang sudah jadi uang masuk,
berapa yang masih menunggu bayar, dan berapa yang belum ditagih" — langsung di satu pivot Sales
Analysis, termasuk penanganan skenario uang muka (down payment) dan credit note. `[HASIL-BACA]`

---

## Scope

### Yang Termasuk (disimpulkan dari kode)

- 3 field baru di `sale.report` (`amount_received`, `amount_to_invoice`, `waiting_for_payment`)
  beserta ekstensi SQL `_select_sale()` + `_group_by_sale()`. `[HASIL-BACA]`
- 3 field stored-compute baru di `sale.order.line` sebagai sumber angka SQL view di atas.
  `[HASIL-BACA]`
- 8 field stored-compute pembantu di `account.move` (`amount_paid`, `amount_paid_cn`, `amount_dp`,
  `amount_dp2`, `amount_dp_nopaid`, `amount_dp2_nopaid`, `amount_refund`, `amount_refund_nopaid`).
  `[HASIL-BACA]`
- Penanganan khusus baris **uang muka** (produk bernama `"Down payment"`) dan **credit note**
  (`move_type == 'out_refund'`), termasuk pembagian proporsional nilai DP ke baris lain.
  `[HASIL-BACA]`
- Konversi mata uang per baris faktur ke mata uang baris SO
  (`invoice_line.currency_id._convert(...)`). `[HASIL-BACA]`

### Yang Tidak Termasuk

- **Tidak ada view/XML sama sekali** — `'data': []` di manifest (satu-satunya entri di-comment).
  Ketiga field `sale.report` hanya muncul sebagai *Measures* di pivot/graph (otomatis, karena
  field numerik), tidak ada kolom/filter yang di-preset. `[HASIL-BACA]`
- **Tidak ada controller aktif** — `controllers/controllers.py` isinya hanya komentar, tapi tetap
  di-import lewat `__init__.py`. `[HASIL-BACA]`
- **Tidak ada model baru** — semua `_inherit`, tidak ada `_name`. Karena itu tidak ada ACL yang
  benar-benar dibutuhkan (lihat F-07 soal `ir.model.access.csv` yang menganggur). `[HASIL-BACA]`
- Tidak ada indikasi eksplisit (komentar/TODO) bahwa ada fitur yang sengaja ditunda. `[HASIL-BACA]`

---

## User Stories (rekonstruksi)

> Ditulis dari sudut pandang kode, bukan wawancara user asli.

### US-01 — Sales manager melihat uang yang benar-benar masuk per produk
Sebagai sales manager, saya membuka **Sales → Reporting → Sales Analysis**, menambahkan measure
*Amount Received*, supaya saya tahu berapa kas yang benar-benar sudah diterima dari tiap
produk/order — bukan sekadar nilai order yang dipesan. `[HASIL-BACA]`

### US-02 — Menemukan order yang sudah difakturkan tapi belum dibayar
Sebagai finance, saya menambahkan measure *Waiting for Payment* untuk memisahkan nilai yang sudah
ditagih tapi uangnya belum masuk, dari nilai yang bahkan belum ditagih. `[HASIL-BACA]`

### US-03 — Menemukan sisa yang belum ditagih
Sebagai finance, saya menambahkan measure *Amount To Invoice* untuk tahu sisa nilai order yang
masih harus difakturkan (nilai baris dikurangi yang sudah diterima dan yang sedang menunggu bayar).
`[HASIL-BACA]`

### US-04 — Order dengan uang muka tetap terhitung benar
Sebagai finance yang memakai skema uang muka, saya berharap baris "Down payment" dan pengurangnya
tidak menggandakan/menghilangkan angka di ketiga metrik di atas. `[HASIL-BACA]`

---

## Business Rules

### BR-01 — `sale.report` mendapat 3 kolom agregat baru
`sale.report` (SQL view, `_auto=False`) menambah kolom `amount_received`, `amount_to_invoice`,
`waiting_for_payment` bertipe `Float(readonly=True)`, diisi dari `SUM(l.<kolom>)` dengan guard
`CASE WHEN l.product_id IS NOT NULL THEN ... ELSE 0 END` — pola guard yang sama dengan kolom
moneter core. `[HASIL-BACA]`
**Lokasi kode:** `advanced_sales_analysis/models/sale_report.py:9-26`
**Catatan tabrakan:** `_select_sale()` dan `_group_by_sale()` KEDUANYA memang ada di core 17.0
(`sale/report/sale_report.py:89` dan `:187`) dan modul memanggil `super()` dengan benar — **tidak
ada override total**. Core juga menyediakan hook resmi `_select_additional_fields()`
(`sale/report/sale_report.py:157`) yang justru dirancang untuk keperluan ini tapi tidak dipakai;
ini pilihan gaya, bukan bug — dicatat di F-08.

### BR-02 — Kolom baru `sale.report` masuk GROUP BY
`_group_by_sale()` menambahkan `l.amount_received, l.waiting_for_payment, l.amount_to_invoice` ke
klausa GROUP BY. `[PERLU-KEPUTUSAN]` → F-06
**Lokasi kode:** `advanced_sales_analysis/models/sale_report.py:14-17`

### BR-03 — `sale.order.line.amount_to_invoice` = sisa yang belum ditagih
Untuk baris ber-`state` `sale`/`done`: hitung `price_subtotal` teoretis dari
`price_unit × (1 − discount/100) × qty` (qty = `qty_delivered` kalau
`invoice_policy == 'delivery'`, selain itu `product_uom_qty`); kalau ada pajak `price_include`,
subtotal diambil dari `tax_id.compute_all(...)['total_excluded']`. Lalu:
- kalau ada baris faktur dengan `discount` BERBEDA dari baris SO → hitung manual
  `max(price_subtotal − Σ nilai baris faktur, 0)`;
- selain itu → **`line.price_subtotal − (waiting_for_payment + amount_received)`**.

Baris di luar `state` `sale`/`done` bernilai `0.0`. `[HASIL-BACA]`
**Lokasi kode:** `advanced_sales_analysis/models/sale_report.py:102-151`
**Catatan:** method ini adalah salinan hampir persis
`sale.order.line._compute_untaxed_amount_to_invoice` core (17.0,
`sale/models/sale_order_line.py:872`) — yang diubah HANYA cabang `else` terakhir: core memakai
`price_subtotal − untaxed_amount_invoiced`, modul memakai
`price_subtotal − (waiting_for_payment + amount_received)`. Nama field/method BEDA dari core
(`amount_to_invoice` vs `untaxed_amount_to_invoice`) → **tidak ada tabrakan nama**.

### BR-04 — `sale.order.line.waiting_for_payment` = nilai tertagih yang belum dibayar
Iterasi baris faktur (`_get_invoice_lines()`) yang `state != 'cancel'` DAN
`payment_state in ('not_paid', 'partial')`:
- `out_invoice` → tambah `amount_residual × (nilai_baris_terkonversi / amount_untaxed)`;
- `out_refund` → kurangi dengan rumus yang sama;
- kalau faktur mengandung baris produk ber-nama mengandung `"Down payment"`, nilai baris
  di-*gross-up* dengan `dp_proportion` dan `amount_residual` dikurangi `amount_dp_nopaid` lebih
  dulu;
- kalau `amount_untaxed == 0` → kontribusi 0 (guard bagi-nol).

Hasil akhir:
- `0` kalau (`amount_residual == 0` ATAU `amount_received == price_subtotal`) DAN produk bukan
  `"Down payment"`;
- `amount_dp_nopaid_dp` (akumulasi DP belum dibayar) kalau produk `"Down payment"`;
- selain itu akumulasi `fixed_waiting_for_payment`. `[PERLU-KEPUTUSAN]` → F-09

**Lokasi kode:** `advanced_sales_analysis/models/sale_report.py:157-200`

### BR-05 — `sale.order.line.amount_received` = nilai tertagih yang sudah dibayar
Iterasi baris faktur `state != 'cancel'` DAN `payment_state in ('paid', 'in_payment', 'partial')`:
- `out_invoice` → tambah `move.amount_paid × (nilai_baris_terkonversi / amount_untaxed)`;
- `out_refund` → kurangi `move.amount_paid_cn × (...)`;
- gross-up `dp_proportion` sama seperti BR-04 kalau faktur punya baris `"Down payment"`.

Hasil akhir:
- `amount_dp_paid` kalau produk `"Down payment"`;
- `0` kalau `amount_paid == 0` dan produk bukan `"Down payment"`;
- selain itu `fix_amount_received`. `[HASIL-BACA]`

**Lokasi kode:** `advanced_sales_analysis/models/sale_report.py:206-246`
**Ketergantungan:** langsung memakai `account.move.amount_paid`/`amount_paid_cn` — yaitu field
yang bertabrakan dengan `account_payment` (F-01). Kalau `account_payment` yang menang di MRO,
`amount_paid` berubah arti jadi "total transaksi pembayaran online", dan seluruh BR-05 ikut salah.

### BR-06 — `account.move.amount_paid` / `amount_paid_cn`
Untuk `out_refund` dengan `payment_state in ('paid','in_payment','partial')` →
`amount_paid_cn = amount_total − amount_residual`.
Untuk `out_invoice` dengan `payment_state` yang sama →
`amount_paid = amount_total − amount_residual`.
**Tidak ada cabang `else`** — kombinasi lain tidak menugaskan nilai apa pun.
`[PERLU-KEPUTUSAN]` → F-01, F-02
**Lokasi kode:** `advanced_sales_analysis/models/sale_report.py:42-49`

### BR-07 — Pemecahan komponen uang muka di `account.move`
`_compute_amount_dp` mengisi 6 field sekaligus, di-reset ke `0.0` tiap iterasi:
- `out_refund`, baris produk `"Down payment"`: `amount_refund` (kalau
  `payment_state in ('paid','in_payment')`) atau `amount_refund_nopaid`;
- `out_invoice`, baris `"Down payment"` dengan `price_subtotal < 0`: `amount_dp` /
  `amount_dp_nopaid`;
- `out_invoice`, baris `"Down payment"` dengan `price_subtotal > 0`: `amount_dp2` /
  `amount_dp2_nopaid`.

Karena penugasan ada DI LUAR loop baris, **hanya baris DP terakhir yang menang** kalau satu faktur
punya lebih dari satu baris uang muka pada kategori yang sama. `[PERLU-KEPUTUSAN]` → F-10
**Lokasi kode:** `advanced_sales_analysis/models/sale_report.py:52-91`
**Catatan:** berbeda dari BR-06, method ini SELALU menugaskan keenam field (nilai default `0.0`
di-set di awal tiap iterasi) — jadi tidak kena masalah "compute tidak assign" F-02.

### BR-08 — `payment_state == 'partial'` dihitung di KEDUA sisi
`payment_state == 'partial'` masuk daftar di BR-04 (waiting) DAN BR-05 (received) — disengaja,
karena faktur terbayar sebagian memang punya porsi di kedua metrik. Tapi di `_compute_amount_dp`
(BR-07) `'partial'` **tidak** termasuk (`payment_state in ('paid','in_payment')` saja), sehingga
faktur DP terbayar sebagian dihitung 100% sebagai "belum dibayar". `[PERLU-KEPUTUSAN]` → F-11
**Lokasi kode:** `advanced_sales_analysis/models/sale_report.py:45, 63, 72, 165, 213`

---

## Catatan Struktur & Kebersihan Kode

- `controllers/controllers.py` kosong (hanya komentar) tapi tetap di-import. `[HASIL-BACA]` → F-12
- `security/ir.model.access.csv` ADA secara fisik tapi entrinya **di-comment** di manifest `data`;
  isinya merujuk `model_advanced_sales_analysis_advanced_sales_analysis` yang tidak pernah
  didefinisikan modul ini. `[PERLU-KEPUTUSAN]` → F-07
- Label field tidak konsisten: `sale.order.line.amount_to_invoice` diberi
  `string='Amount Received'`; empat field `account.move` (`amount_dp`, `amount_dp2`,
  `amount_dp_nopaid`, `amount_dp2_nopaid`) semuanya `string='amount dp'`. `[HASIL-BACA]` → F-13
- `googleaeed8a7b9ec156e7.html` (file verifikasi Google Search Console) ikut di dalam folder addon
  DAN di root repo — tidak ada hubungannya dengan fungsi modul. `[HASIL-BACA]` → F-14
- `self.env['account.move.line'].search(...)` dipanggil di dalam loop bersarang di BR-04 dan BR-05
  → satu query SQL per baris faktur per baris SO. `[HASIL-BACA]` → F-15
