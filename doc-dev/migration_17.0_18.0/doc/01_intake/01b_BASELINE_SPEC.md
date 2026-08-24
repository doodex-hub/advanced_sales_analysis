# Baseline Spec — advanced_sales_analysis

**Step:** 1 — Intake & Scope (pelengkap `01a_MIGRATION_INTAKE.md`)
**Tujuan:** dokumentasikan APA yang modul lakukan (behavior as-is) di 17.0 — sumber kebenaran untuk `05a_MIGRATION_ACCEPTANCE_CRITERIA.md` dan semua testing migrasi (step 9/10/11).
**Tanggal:** 2026-08-21
**Sumber:** Direkonsiliasi dari `FUNCTIONAL_SPEC.md` lama di `source-codebase/doc-dev/backfill/spec/01A_FUNCTIONAL_SPEC.md` + `doc-dev/backfill/FINDINGS.md` (proyek **doc-dev-backfill** terpisah, execution-verified lewat 38 test) + cross-check langsung ke kode `source-codebase` saat ini (`migration/17.0_source` = `backfill/17.0` + fix F-19).

> Semua klaim di bawah dicross-check ulang terhadap `advanced_sales_analysis/models/sale_report.py` di `source-codebase` (dibaca 2026-08-21) — cocok 100% dengan dokumen backfill, tidak ditemukan penyimpangan. Karena itu semua diberi tag `[MATCH]`.

---

## Provenance Tag

Sama seperti skema `migration-tool` (`[MATCH]`/`[GAP]`/`[NO-SPEC]`). Rujukan `(ref: ...)` di sini menunjuk ID asli di dokumen backfill: `BR-NNN` (`01A_FUNCTIONAL_SPEC.md`) atau `F-NNN` (`FINDINGS.md`).

---

## Ringkasan untuk Review — Perlu Konfirmasi User

**Tally:** 23 `[BSL-NNN]`, semua `[MATCH]` (0 `[GAP]`, 0 `[NO-SPEC]`) — dokumen backfill sumbernya sendiri sudah execution-verified (38 test), dan cross-check ulang terhadap kode saat ini tidak menemukan penyimpangan.

1. **`[BSL-006]` (ref BR-06/F-01/F-02):** `account.move.amount_paid` + `_compute_amount_paid` modul ini **bertabrakan nama field DAN method** dengan modul core `account_payment` (yang `auto_install` bareng `account`, jadi SELALU aktif bersama). Siapa yang menang tergantung urutan load registry — behavior ini HARUS dipertahankan identik di 18.0 kecuali pemilik modul memutuskan sebaliknya. **Wajib dicek ulang di Step 2** apakah definisi core `account_payment.amount_paid` berubah di 18.0 (mengubah karakter collision).
2. **`[BSL-013]` (ref F-04):** deteksi baris uang muka memakai string literal hardcoded `"Down payment"` (bukan field resmi `is_downpayment`) — pecah di DB non-English atau nama produk custom. Dipertahankan apa adanya sesuai prinsip migrasi.
3. **`[BSL-008]` (ref BR-03/F-17):** `_compute_amount_to_invoice` punya dead-code path — cabang normal memakai `line.price_subtotal` (field), bukan variabel lokal yang sudah dihitung mempertimbangkan `invoice_policy == 'delivery'`/pajak `price_include`. Untuk produk delivery-based, metrik **Amount To Invoice** overstated. Dibuktikan lewat eksekusi test backfill, prioritas Tinggi.
4. **`[BSL-023]` (ref F-06/F-08/F-19, sudah RESOLVED di source):** implementasi SAAT INI (source `migration/17.0_source`) memakai hook resmi `_select_additional_fields()` — BUKAN override `_select_sale()`/`_group_by_sale()` seperti versi backfill awal. Ini bagian dari baseline yang harus diport (sudah correct/fixed), bukan bug lama yang perlu "direstore".
5. **`[BSL-007]`/`[BSL-021]` (ref F-10, F-03):** ada 2 finding prioritas rendah/sedang terkait akumulasi variabel lokal (`=` vs `+=`) dan `@api.depends` melingkar — dampaknya TIDAK terbukti lewat eksekusi test backfill, tapi tetap dipertahankan apa adanya (bukan sekaligus "dibersihkan" saat migrasi).
6. **15 finding lain masih terbuka** (lihat §8) — semuanya diperlakukan sebagai behavior yang harus identik di 18.0, bukan target perbaikan. Kalau pemilik modul ingin sekalian memperbaiki salah satu SAAT migrasi, itu keputusan eksplisit yang perlu dicatat di `01a_MIGRATION_INTAKE.md` §5 (Scope Boundary) — belum ada permintaan itu sampai saat ini.

---

## 1. Tujuan Modul

Modul memperkaya laporan **Sales Analysis** (`sale.report`) Odoo dengan tiga metrik finansial yang tidak ada di core: **Amount Received** (uang yang benar-benar sudah diterima per baris penjualan), **Waiting for Payment** (nilai yang sudah difakturkan tapi belum dibayar), dan **Amount To Invoice** (sisa yang belum difakturkan sama sekali).

Karena `sale.report` adalah SQL view (`_auto=False`) yang membaca langsung tabel `sale_order_line`, ketiga metrik itu dihitung lebih dulu sebagai field stored-compute di `sale.order.line`, lalu ditarik ke SQL view lewat hook `_select_additional_fields()`. Perhitungannya bertumpu pada delapan field pembantu stored-compute di `account.move` yang memecah nilai faktur ke komponen dibayar/belum dibayar/uang muka/retur.

Tujuan bisnis: menjawab "dari nilai order ini, berapa yang sudah jadi uang masuk, berapa yang masih menunggu bayar, dan berapa yang belum ditagih" langsung di pivot Sales Analysis, termasuk penanganan uang muka (down payment) dan credit note.

## 2. Model & Tanggung Jawab

| Model | Tanggung Jawab |
|---|---|
| `sale.report` (`_inherit`) | SQL view laporan penjualan. Tambah 3 kolom aggregat read-only lewat `_select_additional_fields()`. |
| `account.move` (`_inherit`) | Tambah 8 field stored-compute yang memecah nilai faktur ke komponen dibayar/belum-dibayar/uang-muka/retur — sumber data untuk compute di `sale.order.line`. |
| `sale.order.line` (`_inherit`) | Tambah 3 field stored-compute (`amount_received`, `waiting_for_payment`, `amount_to_invoice`) — metrik utama yang ditarik `sale.report`. |

Tidak ada model baru (`_name`) — seluruhnya `_inherit`. Tidak ada view/XML (`'data': []`).

## 3. Field dengan Makna Bisnis

### `sale.report`
- `amount_received` (Float, readonly) — `SUM` dari `sale.order.line.amount_received` per grup laporan.
- `amount_to_invoice` (Float, readonly) — `SUM` dari `sale.order.line.amount_to_invoice`.
- `waiting_for_payment` (Float, readonly) — `SUM` dari `sale.order.line.waiting_for_payment`.

### `account.move`
- `amount_paid` / `amount_paid_cn` (Float, compute, store) — total dibayar untuk invoice/credit-note.
- `amount_dp` / `amount_dp2` / `amount_dp_nopaid` / `amount_dp2_nopaid` (Float, compute, store) — komponen uang muka (positif/negatif) × (sudah/belum dibayar).
- `amount_refund` / `amount_refund_nopaid` (Float, compute, store) — komponen retur uang muka × (sudah/belum dibayar).

### `sale.order.line`
- `amount_received` (Float, compute, store) — nilai baris SO yang sudah dibayar.
- `waiting_for_payment` (Float, compute, store) — nilai baris SO yang sudah difaktur tapi belum dibayar.
- `amount_to_invoice` (Float, compute, store) — sisa nilai baris SO yang belum difaktur.

## 4. Business Workflow (User Stories, rekonstruksi)

- `[BSL-001]` `[MATCH]` (ref: US-01) Sales manager membuka **Sales → Reporting → Sales Analysis**, menambah measure *Amount Received* untuk tahu kas yang benar-benar sudah diterima per produk/order.
- `[BSL-002]` `[MATCH]` (ref: US-02) Finance menambah measure *Waiting for Payment* untuk memisahkan nilai yang sudah ditagih tapi belum dibayar.
- `[BSL-003]` `[MATCH]` (ref: US-03) Finance menambah measure *Amount To Invoice* untuk tahu sisa nilai order yang masih harus difakturkan.
- `[BSL-004]` `[MATCH]` (ref: US-04) Baris "Down payment" dan pengurangnya tidak boleh menggandakan/menghilangkan angka di ketiga metrik (lihat `[BSL-013]` soal cara deteksinya).

Tidak ada state-transition/action button/wizard — modul murni menambah kolom baca-saja ke laporan pivot yang sudah ada.

## 5. Server-Side Logic dengan Side Effect

- `[BSL-005]` `[MATCH]` (ref: BR-01) `sale.report` mendapat 3 kolom lewat `_select_additional_fields()` (hook resmi core 18.0-compatible, lihat `[BSL-023]`): `res['amount_received']`, `res['waiting_for_payment']`, `res['amount_to_invoice']` — masing-masing `SUM(l.<kolom>)` dengan guard `CASE WHEN l.product_id IS NOT NULL THEN ... ELSE 0 END`.
  **Lokasi:** `models/sale_report.py:9-18`

- `[BSL-006]` `[MATCH]` (ref: BR-06, F-01, F-02) `account.move._compute_amount_paid`: untuk `out_refund` ber-`payment_state in ('paid','in_payment','partial')` → `amount_paid_cn = amount_total - amount_residual`; untuk `out_invoice` kondisi sama → `amount_paid = amount_total - amount_residual`. **Tidak ada cabang `else`** — kombinasi lain (`entry`, `in_invoice`, `in_refund`, `not_paid`, dst) tidak di-assign, tersimpan `NULL` (dikonfirmasi eksekusi: 24 record demo, 0 ter-assign, tidak ada error compute). **Kolusi nama:** field DAN method ini nama-nya identik dengan modul core `account_payment` (`auto_install` bareng `account` → selalu aktif bersama) yang punya semantik BEDA TOTAL (`Monetary`, non-stored, `_compute_amount_paid` dari `transaction_ids`). Siapa yang menang tergantung urutan load registry — dikonfirmasi eksekusi: modul ini yang menang, `account_payment` kehilangan makna aslinya di portal pembayaran.
  **Lokasi:** `models/sale_report.py:22-41`

- `[BSL-007]` `[MATCH]` (ref: BR-07, F-10) `account.move._compute_amount_dp` mengisi 6 field uang-muka (`amount_dp`, `amount_dp2`, `amount_dp_nopaid`, `amount_dp2_nopaid`, `amount_refund`, `amount_refund_nopaid`), di-reset `0.0` tiap iterasi baris faktur (`out_refund`/`out_invoice` × baris produk `"Down payment"` positif/negatif). SELALU menugaskan (tidak kena masalah F-02). Penugasan memakai `=` di dalam loop (bukan `+=`) — kalau satu faktur punya >1 baris DP kategori sama, **hanya baris terakhir yang menang** (dampak belum diukur langsung, prioritas Sedang).
  **Lokasi:** `models/sale_report.py:44-83`

- `[BSL-008]` `[MATCH]` (ref: BR-03, F-17) `sale.order.line._compute_amount_to_invoice`: untuk baris `state in ('sale','done')`, hitung `price_subtotal` lokal mempertimbangkan `invoice_policy` (`qty_delivered` vs `product_uom_qty`) dan pajak `price_include` (`tax_id.compute_all()`). Kalau ada baris faktur dengan `discount` berbeda dari SO → hitung manual `max(price_subtotal - Σ nilai faktur, 0)`. **Cabang normal (mayoritas kasus) memakai FIELD `line.price_subtotal`, BUKAN variabel lokal** yang sudah dihitung — menghapus penanganan `invoice_policy`/pajak di jalur utama. **Dibuktikan eksekusi:** produk `invoice_policy='delivery'`, order 10 kirim 4 → hasil `amount_to_invoice == 100.0` (seharusnya `40.0` menurut logika method sendiri). Prioritas Tinggi, dampak nyata untuk semua produk delivery-based (sangat umum).
  **Lokasi:** `models/sale_report.py:94-135` (implementasi persis; baris di source berbeda sedikit dari nomor lama karena `_select_sale()` sudah dihapus — lihat `[BSL-023]`)

- `[BSL-009]` `[MATCH]` (ref: BR-04, F-09) `sale.order.line._compute_waiting_for_payment_research`: iterasi baris faktur `state != 'cancel'` dan `payment_state in ('not_paid','partial')` → akumulasi `fixed_waiting_for_payment` (tambah untuk `out_invoice`, kurang untuk `out_refund`), dengan gross-up `dp_proportion` kalau faktur punya baris DP. Hasil akhir `0` kalau `amount_residual==0` atau `amount_received==price_subtotal` (dan bukan produk DP); `amount_dp_nopaid_dp` kalau produk DP; selain itu `fixed_waiting_for_payment`. **Catatan non-obvious (dibuktikan TIDAK berdampak lewat eksekusi):** `amount_residual`/`amount_dp_nopaid` di-set ulang (bukan akumulasi) tiap iterasi lalu dipakai lagi setelah loop — secara struktural tidak salah karena filter loop menjamin baris yang lolos selalu punya `amount_residual != 0`, tapi kodenya menyesatkan pembaca.
  **Lokasi:** `models/sale_report.py:141-183`

- `[BSL-010]` `[MATCH]` (ref: BR-05) `sale.order.line._compute_amount_received_research`: pola simetris dengan `[BSL-009]`, iterasi baris faktur `payment_state in ('paid','in_payment','partial')`, akumulasi `fix_amount_received` pakai `move.amount_paid`/`amount_paid_cn` — **bergantung langsung ke field yang berkolisi dengan `account_payment`** (`[BSL-006]`), jadi ikut salah kalau `account_payment` yang menang di MRO.
  **Lokasi:** `models/sale_report.py:189-224`

- `[BSL-011]` `[MATCH]` (ref: BR-08, F-11) Perlakuan `payment_state == 'partial'` **tidak konsisten** antar 4 method: `_compute_amount_paid` & `_compute_waiting_for_payment_research` & `_compute_amount_received_research` menghitung `'partial'`; `_compute_amount_dp` (`[BSL-007]`) TIDAK (`payment_state in ('paid','in_payment')` saja) → faktur DP terbayar sebagian dihitung 100% "belum dibayar", basis `dp_proportion` di `[BSL-009]`/`[BSL-010]` jadi tidak konsisten dengan `amount_paid` faktur yang sama.

- `[BSL-012]` `[MATCH]` (ref: BR-02, historis — lihat `[BSL-023]`) **Tidak berlaku di kode saat ini.** Versi backfill awal (`_group_by_sale()` menambah 3 kolom ke GROUP BY, memecah granularitas laporan) sudah dihapus total oleh fix F-19. Dicatat di sini murni sebagai jejak audit — baseline yang diport ke 18.0 adalah versi TANPA `_group_by_sale()` override.

## 6. Client-Side Behavior

**N/A.** Tidak ada view/XML (`'data': []`), tidak ada controller aktif (`controllers/controllers.py` kosong), tidak ada asset/JS/Owl. Ketiga field `sale.report` muncul otomatis sebagai *Measures* di pivot/graph (default Odoo untuk field numerik), tanpa kolom/filter preset apa pun.

## 7. Dependency Eksternal

### Eksplisit (manifest)
`depends: ['base', 'sale', 'account', 'sale_management']` — keempatnya Native Community, tersedia di 18.0 (dikonfirmasi lewat `native-target`, lihat `01a_MIGRATION_INTAKE.md` §2).

### Implisit/Inferred
- `account_payment` (Native Community, `auto_install: ['account']`) — TIDAK dideklarasikan sebagai dependency, tapi SELALU aktif bareng `account` dan berkolisi nama field/method dengan modul ini (`[BSL-006]`).
- `point_of_sale` (Native Community) — TIDAK dideklarasikan, tapi berbagi hook `_select_additional_fields()` lewat `_select_pos()`-nya sendiri (relevan kalau POS terinstall di environment target — lihat `01a_MIGRATION_INTAKE.md` §2 catatan POS).

## 8. Quirk / Behavior Non-Obvious

- `[BSL-013]` `[MATCH]` (ref: F-04) Deteksi baris uang muka di 9 tempat memakai perbandingan **nama produk** ke string literal `"Down payment"` (sebagian `==`, sebagian `ilike` substring) — BUKAN field resmi `is_downpayment`. Pecah diam-diam di DB non-English (nama produk diterjemahkan) atau produk DP custom; sebaliknya produk non-DP yang mengandung frasa itu bisa salah terdeteksi (karena `ilike`). Prioritas Tinggi.
- `[BSL-014]` `[MATCH]` (ref: F-05) 3 kolom baru `sale.report` **tidak dikonversi mata uang** (`SUM(l.<kolom>)` polos), berbeda dari kolom moneter core yang dibungkus konversi `currency_rate`/`currency_table.rate`. Di DB multi-currency, angka di baris yang sama jadi tidak sebanding. Prioritas Sedang.
- `[BSL-015]` `[MATCH]` (ref: F-07) `security/ir.model.access.csv` ada secara fisik tapi entrinya di-comment di manifest, merujuk model yang tidak pernah didefinisikan modul ini (tidak ada `_name` baru). Kalau di-uncomment, instalasi JUSTRU gagal. Sisa scaffold. Prioritas Sedang.
- `[BSL-016]` `[MATCH]` (ref: F-12) `controllers/controllers.py` kosong (2 baris komentar) tapi tetap di-import dari `__init__.py`. Tidak ada dampak runtime, sisa scaffold. Prioritas Rendah.
- `[BSL-017]` `[MATCH]` (ref: F-13) Label field (`string=`) salah/duplikat — `amount_to_invoice` (SO line) diberi label `'Amount Received'`; 4 field `account.move` semua `string='amount dp'`. Dikonfirmasi eksekusi: Odoo mencatat 13 baris WARNING "same label" saat instalasi, merembet ke UI `account.payment` dan `account.bank.statement.line` (delegasi ke `account.move`). Prioritas Rendah tapi permukaan UI lebih luas dari perkiraan awal.
- `[BSL-018]` `[MATCH]` (ref: F-14) File verifikasi Google Search Console (`googleaeed8a7b9ec156e7.html`) ikut ter-commit di dalam folder addon. Tidak ada dampak runtime, mengotori paket yang didistribusikan (modul ber-`price: 20`).
- `[BSL-019]` `[MATCH]` (ref: F-15) `self.env['account.move.line'].search(...)` dipanggil di dalam loop bersarang (per baris faktur per baris SO) di 2 method compute, padahal bisa diambil dari recordset yang sudah ter-prefetch. Berisiko lambat di database produksi berukuran nyata (belum diukur). Prioritas Sedang.
- `[BSL-020]` `[MATCH]` (ref: F-16) Faktur ber-`amount_untaxed == 0` (guard bagi-nol) selalu berkontribusi `0` ke metrik, walau `amount_residual`-nya bukan nol (kasus tepi: diskon 100% atau faktur full-pajak). Prioritas Rendah.
- `[BSL-021]` `[MATCH]` (ref: F-03) `@api.depends` melingkar antar `amount_to_invoice`/`waiting_for_payment`/`amount_received` di `sale.order.line`. **Dampak TIDAK terbukti** lewat eksekusi (tidak ada penolakan registry, tidak ada order-dependency teramati di test) — diturunkan ke prioritas Rendah, tapi tetap kode yang menyesatkan.
- `[BSL-022]` `[MATCH]` (ref: F-18) Manifest tidak punya key `assets` — modul tidak punya jalur resmi memuat Tour test JS. Bukan bug fungsional (tidak ada JS produksi), tapi membatasi cara testing di masa depan.
- `[BSL-023]` `[MATCH]` (ref: F-06, F-08, F-19 — SEMUA RESOLVED 2026-08-21) **Ini state SAAT INI, bukan bug yang perlu dipertahankan:** implementasi awal (backfill) meng-override `_select_sale()`/`_group_by_sale()` dengan string-concat SQL mentah, yang (a) memecah granularitas laporan (GROUP BY ikut 3 kolom baru) dan (b) gagal di Odoo 17 patch tertentu (production `demo17.doodex.net`) karena UNION dua SELECT `sale.report._query()` jadi punya jumlah kolom berbeda. Fix F-19 menghapus total kedua override, pindah ke hook resmi `_select_additional_fields()` — granularitas kembali identik core (untuk 17.0), UNION selalu sinkron (termasuk dengan `_select_pos()` milik `point_of_sale`, lihat §7). **Source branch migrasi (`migration/17.0_source`) sudah mengandung fix ini** — jadi baseline yang diport ke 18.0 adalah versi POST-fix, bukan versi awal backfill.
  **PENYIMPANGAN DISETUJUI di 18.0 (MF-01, `doc-dev/migration_17.0_18.0/doc/FINDINGS.md`, 2026-08-21):** klaim "granularitas kembali identik core" hanya valid dibandingkan ke core 17.0. Core 18.0 SENDIRI mengubah isi `_group_by_sale()` (menambah `l.price_unit`/`l.invoice_status`/`l.is_downpayment`, menghapus `s.analytic_account_id`) — karena modul ini tidak override method itu, granularitas laporan 18.0 otomatis lebih detail dari 17.0 untuk SO dengan baris produk sama tapi `price_unit`/`invoice_status`/`is_downpayment` berbeda. Ini BUKAN gap yang harus "diperbaiki" supaya identik 17.0 — pemilik modul sudah menyetujui menerima behavior 18.0 apa adanya (Opsi 1 MF-01). Baseline yang benar untuk 18.0: granularitas ikut core 18.0, BUKAN core 17.0.

---

## Cara Pakai

1. Dokumen ini adalah rekonsiliasi 1:1 dari `doc-dev/backfill/spec/01A_FUNCTIONAL_SPEC.md` + `doc-dev/backfill/FINDINGS.md` (proyek doc-dev-backfill terpisah) ke skema ID `BSL-NNN` migration-tool — bukan penulisan ulang independen.
2. Dipakai sebagai input `03_spec/03_MIGRATION_SPEC.md` (strategi teknis port ke 18.0) dan `05_acceptance/05a_MIGRATION_ACCEPTANCE_CRITERIA.md` (tiap AC migrasi wajib sebut `BSL-NNN` yang diverifikasi tetap identik pasca migrasi).
3. ID `BSL-NNN` yang sudah ada TIDAK diubah/dipakai ulang untuk klaim lain sepanjang project migrasi ini, supaya rujukan silang di `03_MIGRATION_SPEC.md`/`05a`/`FINDINGS.md` (migrasi) tidak salah arah.
