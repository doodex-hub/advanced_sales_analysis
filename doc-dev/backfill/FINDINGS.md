# Findings — advanced_sales_analysis

> Satu file konsolidasi — pemilik modul cukup baca file ini untuk tahu semua hal yang butuh
> keputusan manusia. Diisi terus sepanjang proses (Step 01/04/07).
>
> **Prinsip:** temuan dicatat lalu proses LANJUT — bukan berhenti menunggu resolusi satu per satu.
>
> **Dokumen hidup:** kalau pemilik modul memperbaiki kode berdasarkan finding di sini, entry-nya
> ditandai `✅ RESOLVED` + tanggal + bukti test, BUKAN dihapus.

**Modul:** `advanced_sales_analysis` · **Odoo:** 17.0 · **Branch:** `backfill/17.0`
**Terakhir diperbarui:** 2026-08-18 (Step 04 — diverifikasi lewat eksekusi nyata, 36 test)

---

## Ringkasan

Kolom **Bukti**: `baca-kode` = belum diuji; `eksekusi` = dikonfirmasi lewat test/query DB nyata di
Step 04.

| ID | Judul | Tag | Prioritas | Bukti | Status |
|---|---|---|---|---|---|
| F-01 | `amount_paid`/`_compute_amount_paid` bentrok dengan core `account_payment` | `[PERLU-KEPUTUSAN]` | **Tinggi** | eksekusi | Terbuka |
| F-02 | `_compute_amount_paid` tidak assign nilai di semua cabang → tersimpan NULL | `[PERLU-KEPUTUSAN]` | **Tinggi** | eksekusi | Terbuka |
| F-17 | `invoice_policy == 'delivery'` diabaikan — `price_subtotal` lokal dead code | `[PERLU-KEPUTUSAN]` | **Tinggi** | eksekusi | Terbuka |
| F-04 | Deteksi uang muka lewat nama produk hardcoded `"Down payment"` | `[PERLU-KEPUTUSAN]` | **Tinggi** | eksekusi | Terbuka |
| F-05 | Kolom baru `sale.report` tidak dikonversi mata uang | `[PERLU-KEPUTUSAN]` | Sedang | eksekusi | Terbuka |
| F-06 | Kolom baru masuk GROUP BY sekaligus di-SUM | `[PERLU-KEPUTUSAN]` | Sedang | eksekusi | Terbuka |
| F-07 | `ir.model.access.csv` menganggur + merujuk model tak ada | `[PERLU-KEPUTUSAN]` | Sedang | baca-kode | Terbuka |
| F-10 | Baris DP ganda: hanya baris terakhir yang menang | `[PERLU-KEPUTUSAN]` | Sedang | eksekusi | Terbuka |
| F-11 | `payment_state == 'partial'` diperlakukan tidak konsisten | `[PERLU-KEPUTUSAN]` | Sedang | eksekusi | Terbuka |
| F-15 | `search()` di dalam loop bersarang | `[PERLU-KEPUTUSAN]` | Sedang | baca-kode | Terbuka |
| F-03 | Dependency melingkar antar 3 stored compute `sale.order.line` | `[PERLU-KEPUTUSAN]` | ~~Tinggi~~ → **Rendah** | eksekusi | Terbuka — dampak TIDAK terbukti |
| F-09 | `amount_residual` bocor dari iterasi terakhir loop | `[PERLU-KEPUTUSAN]` | ~~Tinggi~~ → **Rendah** | eksekusi | Terbuka — dampak TIDAK terbukti |
| F-08 | Hook resmi `_select_additional_fields()` tidak dipakai | `[PERLU-KEPUTUSAN]` | Rendah | baca-kode | Terbuka |
| F-12 | `controllers/controllers.py` kosong tapi di-import | `[PERLU-KEPUTUSAN]` | Rendah | baca-kode | Terbuka |
| F-13 | Label field salah/duplikat | `[PERLU-KEPUTUSAN]` | Rendah | eksekusi | Terbuka |
| F-14 | File verifikasi Google ikut di dalam addon | `[PERLU-KEPUTUSAN]` | Rendah | baca-kode | Terbuka |
| F-16 | Faktur ber-`amount_untaxed == 0` selalu berkontribusi 0 | `[PERLU-KEPUTUSAN]` | Rendah | eksekusi | Terbuka |
| F-18 | Tidak ada bundle `assets` — modul tidak bisa menampung Tour test | `[PERLU-KEPUTUSAN]` | Rendah | eksekusi | Terbuka |
| F-19 | `_select_sale()` override gagal di Odoo 17 patch tertentu — UNION column mismatch | `[PERLU-KEPUTUSAN]` | **Tinggi** | production | Terbuka |

**Dua koreksi jujur dari Step 04:** F-03 dan F-09 ditulis di Step 01 dengan prioritas Tinggi
berdasarkan pembacaan kode. Eksekusi nyata TIDAK membuktikan dampak yang diduga — keduanya
diturunkan ke Rendah dan alasannya ditulis apa adanya di entry masing-masing, bukan dihapus.

---

## Detail

### F-01 — `amount_paid` + `_compute_amount_paid` bentrok dengan modul core `account_payment`
**Tag:** `[PERLU-KEPUTUSAN]` · **Prioritas:** Tinggi
**Lokasi:** `advanced_sales_analysis/models/sale_report.py:32, 41-49`
**Ref:** BR-06, AC-01-03, AC-02-01
**Deskripsi:** Modul core `account_payment` (Odoo 17.0) mendefinisikan pada model yang SAMA
(`account.move`):

```
amount_paid = fields.Monetary(string="Amount paid", compute='_compute_amount_paid')

@api.depends('transaction_ids')
def _compute_amount_paid(self):
    ...sum transaksi pembayaran ber-state authorized/done...
```
(`account_payment/models/account_move.py:20-40`, diverifikasi lewat
`docker run --rm odoo:17.0`, 2026-08-18)

`advanced_sales_analysis` mendefinisikan **nama field DAN nama method yang persis sama** dengan
semantik berbeda total: `fields.Float(store=True)` berisi `amount_total − amount_residual`.

`account_payment` ber-`auto_install: ['account']` — artinya ia terinstall OTOMATIS di setiap
database yang punya `account` (dependency langsung modul ini). Jadi ini bukan skenario hipotetis:
di kondisi normal keduanya SELALU aktif bersama.

Python meng-override method **by name**, bukan meng-extend seperti `_inherit` di level model. Yang
menang adalah definisi dari modul yang di-load BELAKANGAN di registry. Kedua modul tidak saling
`depends`, jadi urutan relatifnya tidak dikunci oleh graf dependency — bisa berbeda antar database.
**Dampak:**
- Kalau `advanced_sales_analysis` menang: `account_payment` kehilangan angka "Amount paid" di
  portal pembayaran dan di `_has_to_be_paid()` — nilainya berubah jadi total-dikurangi-sisa, bukan
  total transaksi pembayaran online. Field juga berubah dari non-stored `Monetary` jadi stored
  `Float` (kolom fisik baru di tabel).
- Kalau `account_payment` menang: `_compute_amount_paid` versi core dipakai, sehingga
  `amount_paid_cn` (field milik modul ini yang juga di-`compute='_compute_amount_paid'`) **tidak
  pernah di-assign sama sekali** → error compute-tidak-assign; dan seluruh BR-05
  (`amount_received`) memakai angka dengan arti yang salah.
- Tidak ada error/warning di log instalasi untuk kelas bug ini — hanya ketahuan lewat pengecekan
  nama eksplisit.

**Bukti eksekusi (Step 04, 2026-08-18) — dugaan TERKONFIRMASI, dan yang menang adalah modul ini:**

```sql
SELECT name, state FROM ir_module_module WHERE name = 'account_payment';
--  account_payment | installed          <- benar-benar ikut terinstall

SELECT f.name, f.ttype, f.store FROM ir_model_fields f
  JOIN ir_model m ON m.id = f.model_id
 WHERE m.model = 'account.move' AND f.name = 'amount_paid';
--  amount_paid | float | t              <- definisi advanced_sales_analysis
--  (definisi account_payment seharusnya: monetary | store = f)
```

Kolom fisik `amount_paid double precision` juga dibuat di tabel `account_move` — konsekuensi
`store=True` modul ini terhadap field core yang aslinya non-stored. Test
`test_ac_01_03_semantik_amount_paid_bukan_semantik_account_payment` membuktikan semantiknya juga
ikut tergantikan: invoice tanpa satu pun `payment.transaction` tetap melaporkan
`amount_paid == 100.0` (semantik modul ini), bukan `0.0` (semantik `account_payment`).

**Dampak nyata yang sekarang pasti, bukan lagi hipotetis:** setiap fitur `account_payment` yang
membaca `invoice.amount_paid` — portal pembayaran pelanggan, `_has_to_be_paid()`, tampilan
"Amount paid" di portal — sekarang memakai angka `amount_total − amount_residual` alih-alih total
transaksi pembayaran online yang authorized/done. Untuk invoice yang dibayar lewat transfer bank
manual (tanpa transaksi online sama sekali), kedua angka itu berbeda jauh.

**Rekomendasi:** ganti nama kedua field dan kedua method ke namespace modul sendiri (mis.
`x_asa_amount_paid` / `_compute_asa_amount_paid`). Kalau memang niatnya memakai angka
`account_payment`, jangan redefinisi — baca field core itu apa adanya.
**Referensi knowledge:** `doc-dev-backfill/knowledge/odoo/method_override_collision_with_core.md`
**Keputusan pemilik modul:** *(kosong — diisi manusia)*

---

### F-02 — `_compute_amount_paid` tidak menugaskan nilai di semua cabang
**Tag:** `[PERLU-KEPUTUSAN]` · **Prioritas:** Tinggi
**Lokasi:** `advanced_sales_analysis/models/sale_report.py:42-49`
**Ref:** BR-06, AC-02-03, AC-02-04
**Deskripsi:** Method hanya meng-assign di dalam dua `if` bersarang:

```
if move.move_type == "out_refund":
    if move.payment_state in [...]:
        move.amount_paid_cn = ...
elif move.move_type == "out_invoice":
    if move.payment_state in [...]:
        move.amount_paid = ...
```

Tidak ada `else`, dan tidak ada nilai default sebelum percabangan. Kombinasi yang TIDAK
ter-cover: `move_type` `entry` / `in_invoice` / `in_refund` / `out_receipt` / `in_receipt`
(semua jurnal & tagihan pemasok), dan `out_invoice`/`out_refund` dengan
`payment_state == 'not_paid'` atau `'reversed'` / `'invoicing_legacy'`. Selain itu, di cabang
`out_invoice` `amount_paid_cn` tidak pernah di-assign (dan sebaliknya) — padahal KEDUA field
memakai method compute yang sama.
**Dampak — DIKOREKSI setelah eksekusi nyata (Step 04, 2026-08-18):** dugaan awal Step 01 adalah
Odoo akan melempar error "Compute method failed to assign". **Itu TIDAK terjadi.** Yang benar-benar
terjadi:

- Instalasi modul di database dengan demo data **berhasil bersih**, tanpa traceback.
- Semua 24 `account.move` demo mendapat `amount_paid` dan `amount_paid_cn` bernilai **`NULL`** di
  database — nol dari 24 yang ter-assign:

  ```
   move_type  | payment_state | n  | amount_paid_notnull | cn_notnull
  -------------+---------------+----+---------------------+------------
   entry       | not_paid      | 10 |                   0 |          0
   in_invoice  | not_paid      |  3 |                   0 |          0
   in_refund   | not_paid      |  2 |                   0 |          0
   out_invoice | not_paid      |  4 |                   0 |          0
   out_refund  | not_paid      |  5 |                   0 |          0
  ```

- Membuat jurnal umum baru (`move_type == 'entry'`) juga tidak error; kolomnya tersimpan `NULL` dan
  dibaca `0.0` dari Python (test `test_ac_02_03_move_type_entry_tidak_assign`).

Jadi ini **bukan** bug yang memutus operasi akuntansi seperti diduga semula. Yang tersisa tetap
nyata tapi lebih halus: `amount_paid` menyimpan `NULL` alih-alih `0.0` untuk mayoritas record.
`NULL` berperilaku berbeda dari `0.0` di agregasi SQL (`SUM`/`AVG` mengabaikan `NULL`, dan
`NULL + x` menghasilkan `NULL`) — dan `sale.report` modul ini memang mengagregasi kolom-kolom
turunannya lewat SQL langsung. Prioritas tetap Tinggi karena field ini juga yang menimpa definisi
`account_payment` (F-01).
**Rekomendasi:** set default `move.amount_paid = 0.0` dan `move.amount_paid_cn = 0.0` di awal tiap
iterasi (pola yang sudah dipakai dengan benar di `_compute_amount_dp`, lihat BR-07).
**Keputusan pemilik modul:** *(kosong — diisi manusia)*

---

### F-03 — Dependency melingkar antar tiga stored compute di `sale.order.line`
**Tag:** `[PERLU-KEPUTUSAN]` · **Prioritas:** ~~Tinggi~~ → **Rendah** (diturunkan setelah eksekusi)
**Lokasi:** `advanced_sales_analysis/models/sale_report.py:101, 153-156, 202-205`
**Ref:** BR-03, BR-04, BR-05, AC-06-05
**Deskripsi:** Ketiga field stored-compute saling menyebut satu sama lain di `@api.depends`:

| Field | `@api.depends` menyebut | Ditulis oleh |
|---|---|---|
| `amount_to_invoice` | `waiting_for_payment`, `amount_received` | `_compute_amount_to_invoice` |
| `waiting_for_payment` | `amount_received`, `amount_to_invoice` | `_compute_waiting_for_payment_research` |
| `amount_received` | `waiting_for_payment`, `amount_to_invoice` | `_compute_amount_received_research` |

Selain itu `_compute_waiting_for_payment_research` juga men-`depends` ke `waiting_for_payment`
(field yang ditulisnya sendiri, `:101` menyebut `waiting_for_payment` untuk
`_compute_amount_to_invoice`, dan `:202` menyebut `waiting_for_payment` untuk
`_compute_amount_received_research`).
**Dampak:** setiap perubahan pada salah satu field memicu invalidasi dua lainnya, yang balik
memicu yang pertama. Kemungkinan hasilnya: (a) Odoo mendeteksi siklus saat setup registry dan
menolak/memperingatkan, (b) rekomputasi berulang yang boros, atau (c) nilai akhir yang bergantung
pada urutan evaluasi — dua database dengan data identik bisa menghasilkan angka berbeda. Yang mana
dari ketiganya perlu dibuktikan lewat eksekusi nyata di Step 04.
Perhatikan juga bahwa nilai `amount_to_invoice` memang secara matematis diturunkan dari dua yang
lain (BR-03: `price_subtotal − (waiting + received)`) — jadi arah dependency satu arah
(`received`/`waiting` → `to_invoice`) mungkin memang yang diinginkan, dan arah baliknya yang
berlebih.
**Bukti eksekusi (Step 04, 2026-08-18) — dampak yang diduga TIDAK terbukti:** ketiga kemungkinan
yang ditulis di Step 01 diuji dan tidak satu pun muncul:
- Odoo **tidak** menolak/memperingatkan siklus saat setup registry — modul terinstall bersih.
- Test `test_ac_06_05_urutan_pembacaan_field_melingkar` membaca ketiga field dalam DUA urutan
  berbeda (dengan `invalidate_recordset()` di antaranya) dan mendapat hasil **identik** — tidak
  ada order-dependency yang teramati.
- 36 test lain tidak menunjukkan gejala rekomputasi berulang yang mencolok.

Prioritas diturunkan ke **Rendah**. Ini tetap dicatat (bukan dihapus) karena `@api.depends`
melingkar tetap kode yang menyesatkan pembaca dan menyimpan risiko kalau nanti salah satu compute
diubah — tapi TIDAK boleh dilaporkan sebagai bug aktif berdasarkan bukti yang ada.
**Rekomendasi:** buang `amount_to_invoice` dari `@api.depends` milik
`_compute_waiting_for_payment_research` dan `_compute_amount_received_research`, serta buang
referensi self-depends; sisakan hanya arah `received`/`waiting` → `to_invoice`. Sifatnya
kebersihan kode, bukan perbaikan bug.
**Keputusan pemilik modul:** *(kosong — diisi manusia)*

---

### F-04 — Deteksi baris uang muka lewat nama produk hardcoded `"Down payment"`
**Tag:** `[PERLU-KEPUTUSAN]` · **Prioritas:** Tinggi
**Lokasi:** `advanced_sales_analysis/models/sale_report.py:62, 71, 78, 172, 195, 197, 219, 241, 243`
**Ref:** BR-04, BR-05, BR-07, AC-03-05
**Deskripsi:** Sembilan tempat mendeteksi baris uang muka dengan membandingkan **nama produk** ke
string literal `"Down payment"` — sebagian dengan `==` (`line.product_id.name == "Down payment"`,
`line.product_template_id.name != "Down payment"`), sebagian dengan
`('product_id.name', 'ilike', 'Down payment')`. Odoo sendiri menandai baris uang muka lewat field
boolean `is_downpayment` di `sale.order.line` (dan produk DP dirujuk lewat parameter konfigurasi
`sale.default_deposit_product_id`), bukan lewat nama.
**Dampak:** di database berbahasa non-Inggris nama produk DP diterjemahkan (mis. `"Acompte"` di
Prancis — relevan karena repo ini punya `LISEZMOI.md` berbahasa Prancis), atau perusahaan menamai
produk DP-nya sendiri. Di kasus itu SELURUH logika uang muka mati diam-diam: `amount_dp*` tetap
`0.0`, gross-up `dp_proportion` tidak pernah aktif, dan cabang khusus DP di BR-04/BR-05 tidak
pernah dipilih — tanpa error apa pun. Sebaliknya, produk non-DP yang kebetulan mengandung frasa
"Down payment" akan salah dianggap DP (karena `ilike` di `:172`/`:219` adalah substring match,
tidak konsisten dengan `==` di tempat lain).
**Rekomendasi:** pakai `line.is_downpayment` (`sale.order.line`) dan, untuk sisi faktur,
`line.sale_line_ids.is_downpayment` atau perbandingan ke
`self.env['ir.config_parameter'].sudo().get_param('sale.default_deposit_product_id')`.
**Keputusan pemilik modul:** *(kosong — diisi manusia)*

---

### F-05 — Kolom baru `sale.report` tidak dikonversi mata uang
**Tag:** `[PERLU-KEPUTUSAN]` · **Prioritas:** Sedang
**Lokasi:** `advanced_sales_analysis/models/sale_report.py:20-26`
**Ref:** BR-01, AC-07-04
**Deskripsi:** Semua kolom moneter core di `_select_sale()` dibungkus konversi mata uang:
`SUM(l.price_subtotal / CASE COALESCE(s.currency_rate,0) WHEN 0 THEN 1.0 ELSE s.currency_rate END
* CASE COALESCE(currency_table.rate,0) ... END)`. Tiga kolom baru modul ini memakai `SUM(l.<kolom>)`
polos tanpa pembagi/pengali itu.
**Dampak:** di database multi-mata-uang, satu baris laporan menampilkan `price_subtotal` dalam mata
uang perusahaan tapi `amount_received`/`waiting_for_payment`/`amount_to_invoice` dalam mata uang
order — angka di baris yang sama tidak sebanding, dan agregat lintas order beda mata uang
menjumlahkan satuan yang berbeda. Perlu dicatat: nilai di level `sale.order.line` SUDAH dikonversi
sekali (`invoice_line.currency_id._convert(...)` ke `line.currency_id`, yaitu mata uang order) —
jadi yang hilang persis satu lapis konversi terakhir order → perusahaan.
**Rekomendasi:** bungkus ketiga kolom dengan pola `_case_value_or_one('s.currency_rate')` /
`_case_value_or_one('currency_table.rate')` yang sama seperti kolom core.
**Keputusan pemilik modul:** *(kosong — diisi manusia)*

---

### F-06 — Kolom baru masuk GROUP BY sekaligus dibungkus `SUM()`
**Tag:** `[PERLU-KEPUTUSAN]` · **Prioritas:** Sedang
**Lokasi:** `advanced_sales_analysis/models/sale_report.py:14-17` (GROUP BY) vs `:20-26` (SELECT)
**Ref:** BR-01, BR-02, AC-07-03
**Deskripsi:** `_group_by_sale()` menambahkan `l.amount_received, l.waiting_for_payment,
l.amount_to_invoice` ke GROUP BY, sementara `_select_sale()` membungkus ketiganya dengan `SUM()`.
Dua konsekuensi:
1. `SUM(x)` atas kolom yang ikut di-GROUP BY tidak menjumlahkan apa pun — hasilnya nilai kolom itu
   sendiri dikali jumlah baris dalam grup, dan karena grup sekarang unik per nilai kolom itu,
   efektifnya sama dengan nilai aslinya. Ekspresi `SUM()`-nya jadi menyesatkan.
2. Granularitas laporan berubah: GROUP BY core mengelompokkan per (produk, order, diskon, …).
   Dengan tiga kolom tambahan ini, dua baris SO yang tadinya menyatu jadi satu row laporan akan
   TERPECAH kalau salah satu dari ketiga nilai itu berbeda — ini mengubah perilaku laporan core,
   bukan hanya menambah kolom.

**Dampak:** jumlah baris di Sales Analysis bisa bertambah dibanding tanpa modul ini, memengaruhi
juga kolom-kolom core (`nbr`, `product_uom_qty`, dst) yang ikut terpecah. Perlu dibuktikan lewat
data uji di Step 04/07.
**Rekomendasi:** hapus ketiga kolom dari `_group_by_sale()` dan biarkan `SUM()` di SELECT bekerja
sebagaimana mestinya; grain laporan kembali identik dengan core.
**Keputusan pemilik modul:** *(kosong — diisi manusia)*

---

### F-07 — `security/ir.model.access.csv` menganggur dan merujuk model yang tidak ada
**Tag:** `[PERLU-KEPUTUSAN]` · **Prioritas:** Sedang
**Lokasi:** `advanced_sales_analysis/security/ir.model.access.csv:2`,
`advanced_sales_analysis/__manifest__.py` key `data`
**Deskripsi:** File ACL ada secara fisik tapi entrinya **di-comment** di manifest
(`# 'security/ir.model.access.csv',`) sehingga tidak pernah dimuat. Isinya merujuk
`model_advanced_sales_analysis_advanced_sales_analysis` — ID model yang tidak pernah didefinisikan
modul ini (modul hanya `_inherit`, tidak ada `_name` baru). Ini persis pola "file data tidak
terdaftar di manifest, gagal diam-diam" di knowledge base BACKFILL, dengan twist: kalau entri itu
DI-UNCOMMENT, instalasi justru akan GAGAL karena `model_id:id` menunjuk XML ID yang tidak ada.
**Dampak:** saat ini nol (file diabaikan). Risikonya adalah jebakan untuk dev berikutnya yang
melihat file ACL dan mengira modul butuh ACL, lalu mengaktifkannya dan memecah instalasi. Sisa
scaffold `odoo scaffold` yang tidak dibersihkan.
**Rekomendasi:** hapus file `security/ir.model.access.csv` beserta folder `security/`, dan hapus
baris komentarnya dari manifest.
**Referensi knowledge:**
`doc-dev-backfill/knowledge/odoo/data_file_not_registered_in_manifest_silent.md`
**Keputusan pemilik modul:** *(kosong — diisi manusia)*

---

### F-08 — Hook resmi `_select_additional_fields()` tidak dipakai
**Tag:** `[PERLU-KEPUTUSAN]` · **Prioritas:** Rendah
**Lokasi:** `advanced_sales_analysis/models/sale_report.py:19-26`
**Ref:** BR-01
**Deskripsi:** Core `sale.report` (17.0) menyediakan hook `_select_additional_fields()` yang
mengembalikan `dict` `{nama_field: ekspresi_sql}` dan otomatis dirangkai jadi `%s AS %s`
(`sale/report/sale_report.py:157-165`). Modul memilih meng-override `_select_sale()` dan
menyambung string SQL mentah dengan `+`.
**Dampak:** fungsional setara hari ini, tapi lebih rapuh terhadap perubahan core (kalau core
mengubah ekor `_select_sale()`, penyambungan string bisa menghasilkan SQL invalid) dan lebih
mudah bentrok kalau modul lain melakukan hal yang sama. Bukan bug — pilihan gaya yang menyimpang
dari API yang disediakan.
**Rekomendasi:** pindahkan ketiga kolom ke `_select_additional_fields()`. Catatan: `_group_by_sale`
tetap perlu di-override kalau F-06 diputuskan tetap dipertahankan.
**Keputusan pemilik modul:** *(kosong — diisi manusia)*

---

### F-09 — `amount_residual` (dan `amount_dp_nopaid`) bocor dari iterasi terakhir loop
**Tag:** `[PERLU-KEPUTUSAN]` · **Prioritas:** ~~Tinggi~~ → **Rendah** (diturunkan setelah eksekusi)
**Lokasi:** `advanced_sales_analysis/models/sale_report.py:162, 168, 170, 195`
**Ref:** BR-04, AC-05-05
**Deskripsi:** Variabel `amount_residual` dan `amount_dp_nopaid` di-set ULANG (bukan diakumulasi)
di setiap iterasi baris faktur (`:168`, `:170`), tapi dipakai lagi SETELAH loop selesai, di guard
penentu hasil akhir:

```
if (amount_residual == 0 or line.amount_received == line.price_subtotal) and ...:
    line.waiting_for_payment = 0
```

Nilainya karena itu berasal dari baris faktur TERAKHIR yang lolos filter — bukan dari seluruh
baris faktur baris SO tersebut. Kalau tidak ada baris faktur yang lolos sama sekali, nilainya
tetap `0.0` dari inisialisasi, sehingga guard langsung memaksa `waiting_for_payment = 0`.
Bandingkan dengan `amount_dp_nopaid_dp` di baris yang sama yang memang diakumulasi dengan `+=`
(`:169`) — inkonsistensi ini menguatkan dugaan `:168`/`:170` tidak disengaja.
**Dampak — DIKOREKSI setelah eksekusi (Step 04, 2026-08-18):** dugaan Step 01 adalah
`waiting_for_payment` bisa dipaksa jadi `0` walau masih ada tagihan terbuka. Test
`test_ac_05_05_dua_faktur_untuk_satu_baris_so` (satu baris SO 2×100, faktur A lunas, faktur B
belum dibayar) mendapat `waiting_for_payment == 100.0` dan `amount_received == 100.0` — **benar,
bukan 0**.

Alasan strukturalnya, yang terlewat saat Step 01: filter loop hanya meloloskan baris faktur
ber-`payment_state` `not_paid`/`partial`, dan faktur semacam itu **selalu** punya
`amount_residual != 0`. Jadi begitu ada satu saja baris faktur yang lolos, `amount_residual`
pasca-loop pasti bukan nol dan guard tidak pernah aktif. Kalau tidak ada yang lolos sama sekali,
`amount_residual` tetap `0.0` dari inisialisasi dan guard memaksa `waiting = 0` — yang memang
hasil yang benar untuk kasus itu.

Prioritas diturunkan ke **Rendah**: yang tersisa adalah kode yang menyesatkan (variabel dipakai di
luar scope loop-nya, dan tidak konsisten dengan `amount_dp_nopaid_dp` tetangganya yang justru
memakai `+=`), bukan bug dengan dampak terbukti.
**Rekomendasi:** akumulasi `amount_residual` (mis. `total_residual += ...`) atau evaluasi guard di
dalam loop, bukan di luar — sebagai kebersihan kode.
**Keputusan pemilik modul:** *(kosong — diisi manusia)*

---

### F-10 — Faktur dengan lebih dari satu baris uang muka: hanya baris terakhir yang menang
**Tag:** `[PERLU-KEPUTUSAN]` · **Prioritas:** Sedang
**Lokasi:** `advanced_sales_analysis/models/sale_report.py:60-91`
**Ref:** BR-07, AC-03-03
**Deskripsi:** Di `_compute_amount_dp`, penugasan ke enam variabel lokal memakai `=` (bukan `+=`)
di dalam loop `for line in move.invoice_line_ids`, dan penugasan ke field dilakukan setelah loop.
Kalau satu faktur punya dua baris DP pada kategori yang sama (mis. dua termin uang muka positif),
hanya nilai dari baris terakhir yang tersimpan.
**Dampak:** nilai `amount_dp*` lebih kecil dari seharusnya untuk faktur multi-DP, yang lalu
merambat ke `dp_proportion` di BR-04/BR-05 dan ke angka laporan. Skenario multi-DP tidak umum tapi
sah secara bisnis (uang muka bertahap).
**Rekomendasi:** ganti ke `+=` untuk keenam akumulator.
**Keputusan pemilik modul:** *(kosong — diisi manusia)*

---

### F-11 — `payment_state == 'partial'` diperlakukan tidak konsisten antar method
**Tag:** `[PERLU-KEPUTUSAN]` · **Prioritas:** Sedang
**Lokasi:** `advanced_sales_analysis/models/sale_report.py:45, 48` vs `:63, 72, 79` vs `:165, 213`
**Ref:** BR-08, AC-03-04
**Deskripsi:** Tiga daftar `payment_state` berbeda dipakai di modul yang sama:

| Method | Daftar | Konsekuensi |
|---|---|---|
| `_compute_amount_paid` | `['paid', 'in_payment', 'partial']` | partial dihitung |
| `_compute_amount_dp` | `['paid', 'in_payment']` | partial dianggap belum dibayar |
| `_compute_waiting_for_payment_research` | `'not_paid'` atau `'partial'` | partial dihitung |
| `_compute_amount_received_research` | `['paid', 'in_payment', 'partial']` | partial dihitung |

Faktur uang muka yang terbayar sebagian karena itu masuk `amount_dp2_nopaid` (100% dianggap belum
dibayar) sementara `amount_paid` untuk faktur yang sama sudah mencatat porsi terbayarnya.
**Dampak:** untuk skenario uang muka + pembayaran sebagian, `dp_proportion` di BR-04/BR-05 dihitung
dari basis yang tidak konsisten dengan `amount_paid` — hasil `amount_received` dan
`waiting_for_payment` bisa saling tumpang tindih atau menyisakan selisih.
**Rekomendasi:** samakan perlakuan `'partial'` di keempat method, atau dokumentasikan eksplisit
kenapa `_compute_amount_dp` sengaja berbeda.
**Keputusan pemilik modul:** *(kosong — diisi manusia)*

---

### F-12 — `controllers/controllers.py` kosong tapi tetap di-import
**Tag:** `[PERLU-KEPUTUSAN]` · **Prioritas:** Rendah
**Lokasi:** `advanced_sales_analysis/controllers/controllers.py`,
`advanced_sales_analysis/__init__.py:3`
**Deskripsi:** File hanya berisi dua baris komentar (`# from odoo import http`). Paket
`controllers` tetap di-import dari `__init__.py`. Sisa `odoo scaffold` yang tidak dibersihkan,
sama seperti F-07.
**Dampak:** tidak ada dampak runtime. Menambah noise dan memberi kesan modul punya endpoint HTTP
padahal tidak.
**Rekomendasi:** hapus folder `controllers/` dan barisnya di `__init__.py`.
**Keputusan pemilik modul:** *(kosong — diisi manusia)*

---

### F-13 — Label field (`string=`) salah dan duplikat
**Tag:** `[PERLU-KEPUTUSAN]` · **Prioritas:** Rendah
**Lokasi:** `advanced_sales_analysis/models/sale_report.py:34-37, 98`
**Deskripsi:**
- `sale.order.line.amount_to_invoice` diberi `string='Amount Received'` — label milik field lain.
- `amount_dp`, `amount_dp2`, `amount_dp_nopaid`, `amount_dp2_nopaid` keempatnya
  `string='amount dp'`; `amount_refund` dan `amount_refund_nopaid` keduanya `string='amount refund'`.
  Semuanya juga huruf kecil, tidak mengikuti konvensi Title Case Odoo.

**Bukti eksekusi (Step 04, 2026-08-18):** Odoo sendiri sudah memperingatkan ini di log instalasi —
13 baris `WARNING odoo.addons.base.models.ir_model: Two fields (...) have the same label`. Yang
tidak terduga dari baca kode: peringatan itu **tidak hanya untuk `account.move`**, tapi ikut
merembet ke `account.payment` dan `account.bank.statement.line` (kedua model itu mendelegasikan ke
`account.move`), dengan atribusi `[Modules: None and None]`:

```
Two fields (amount_dp2, amount_dp) of account.move() have the same label: amount dp.
Two fields (amount_dp2, amount_dp) of account.payment() have the same label: amount dp.
Two fields (amount_dp2, amount_dp) of account.bank.statement.line() have the same label: amount dp.
Two fields (amount_to_invoice, amount_received) of sale.order.line() have the same label: Amount Received.
```

Artinya kedelapan field `account.move` modul ini juga ikut muncul di UI `account.payment` dan
`account.bank.statement.line` — permukaan yang lebih luas dari yang diduga di Step 01.
**Dampak:** field-field ini muncul di UI (dropdown Measures pivot `account.move`, Add Custom Filter,
export) dengan nama yang tidak bisa dibedakan satu sama lain — user tidak bisa tahu mana yang mana.
**Rekomendasi:** beri label unik dan deskriptif, mis. `'Down Payment (Paid, Deducted)'`,
`'Down Payment (Unpaid, Deducted)'`, dst.
**Keputusan pemilik modul:** *(kosong — diisi manusia)*

---

### F-14 — File verifikasi Google Search Console ikut di dalam addon
**Tag:** `[PERLU-KEPUTUSAN]` · **Prioritas:** Rendah
**Lokasi:** `advanced_sales_analysis/googleaeed8a7b9ec156e7.html` (dan salinannya di root repo)
**Deskripsi:** File verifikasi kepemilikan domain Google ikut ter-commit di dalam folder addon,
tidak berhubungan dengan fungsi modul.
**Dampak:** tidak ada dampak runtime (Odoo tidak menyajikan file ini). Mengotori paket yang
didistribusikan (modul ini ber-`price: 20` di manifest, jadi kemungkinan didistribusikan ke pihak
ketiga).
**Rekomendasi:** hapus dari dalam folder addon; pertahankan di root repo hanya kalau memang ada
alasannya.
**Keputusan pemilik modul:** *(kosong — diisi manusia)*

---

### F-15 — `search()` dipanggil di dalam loop bersarang
**Tag:** `[PERLU-KEPUTUSAN]` · **Prioritas:** Sedang
**Lokasi:** `advanced_sales_analysis/models/sale_report.py:171-172, 219`
**Deskripsi:** `self.env['account.move.line'].search([...])` dipanggil di dalam
`for invoice_line in line._get_invoice_lines()` yang sendiri berada di dalam `for line in self` —
satu query SQL terpisah per baris faktur per baris SO, di kedua method compute. Query itu selalu
mencari hal yang sama (apakah faktur ini punya baris DP) dan bisa diambil dari
`invoice_line.move_id.invoice_line_ids` yang sudah ter-prefetch.
**Dampak:** `sale.order.line` adalah tabel besar dan ketiga field ini stored — artinya method
compute ini juga berjalan saat instalasi/upgrade modul (recompute massal seluruh baris SO
existing) dan setiap kali faktur berubah. Pada database produksi berukuran nyata, ini berpotensi
membuat instalasi/upgrade sangat lambat. Belum diukur — perlu observasi waktu instalasi di
Step 04.
**Rekomendasi:** ganti `search()` dengan filter atas recordset yang sudah ada, mis.
`invoice_line.move_id.invoice_line_ids.filtered(lambda l: l.product_id.is_downpayment)` (setelah
F-04 diselesaikan).
**Keputusan pemilik modul:** *(kosong — diisi manusia)*

---

### F-16 — Faktur ber-`amount_untaxed == 0` selalu berkontribusi 0
**Tag:** `[PERLU-KEPUTUSAN]` · **Prioritas:** Rendah
**Lokasi:** `advanced_sales_analysis/models/sale_report.py:175-176, 186-187, 222-223, 232-233`
**Ref:** BR-04, BR-05, AC-04-07
**Deskripsi:** Guard bagi-nol menuliskan `fixed_waiting_for_payment += 0` /
`fix_amount_received -= 0` — secara teknis benar mencegah `ZeroDivisionError`, tapi berarti faktur
ber-untaxed-nol (mis. 100% diskon, atau faktur yang seluruh nilainya pajak) tidak pernah
berkontribusi ke metrik mana pun, walau `amount_residual`-nya bukan nol.
**Dampak:** kasus tepi; angka laporan kehilangan kontribusi faktur semacam itu tanpa jejak.
**Rekomendasi:** putuskan apakah basis proporsi seharusnya `amount_total` (bukan `amount_untaxed`)
untuk kasus ini, atau memang sengaja diabaikan — kalau sengaja, beri komentar di kode.
**Keputusan pemilik modul:** *(kosong — diisi manusia)*

---

### F-17 — `invoice_policy == 'delivery'` diabaikan: `price_subtotal` lokal jadi dead code
**Tag:** `[PERLU-KEPUTUSAN]` · **Prioritas:** Tinggi · **Ditemukan:** Step 04 (eksekusi), bukan
Step 01 (baca kode)
**Lokasi:** `advanced_sales_analysis/models/sale_report.py:118-121, 149`
**Ref:** BR-03, AC-06-04
**Deskripsi:** `_compute_amount_to_invoice` menghitung variabel lokal `price_subtotal` dengan
susah payah — memilih `qty_delivered` vs `product_uom_qty` sesuai `invoice_policy`, lalu
memanggil `tax_id.compute_all(...)` kalau ada pajak `price_include`:

```python
uom_qty_to_consider = line.qty_delivered if line.product_id.invoice_policy == 'delivery' else line.product_uom_qty
price_reduce = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
price_subtotal = price_reduce * uom_qty_to_consider
if len(line.tax_id.filtered(lambda tax: tax.price_include)) > 0:
    price_subtotal = line.tax_id.compute_all(...)['total_excluded']
```

Tapi variabel itu **hanya dipakai di cabang `if`** (kasus "diskon baris faktur berbeda dari baris
SO"). Cabang `else` — yang jalan untuk hampir semua kasus normal — memakai **FIELD**
`line.price_subtotal`, bukan variabel lokalnya:

```python
amount_to_invoice = line.price_subtotal - (line.waiting_for_payment + line.amount_received)
```

Di core Odoo (`sale/models/sale_order_line.py:915`), cabang `else`-nya memakai variabel lokal itu
(`price_subtotal - line.untaxed_amount_invoiced`). Perubahan modul ini ke `line.price_subtotal`
menghapus seluruh penanganan `invoice_policy`/`price_include` di jalur utama tanpa disadari.
**Bukti eksekusi:** produk ber-`invoice_policy == 'delivery'`, 10 dipesan @10, baru 4 dikirim.
Nilai yang benar menurut logika yang dihitung method itu sendiri adalah `4 × 10 = 40`. Hasil
sebenarnya: **`amount_to_invoice == 100.0`** (`test_ac_06_04_invoice_policy_delivery_diabaikan`).
Ini yang membuat run pertama Step 04 gagal — assertion-nya kemudian diperbaiki untuk merekam
perilaku nyata, sesuai prinsip BACKFILL.
**Dampak:** untuk semua produk ber-`invoice_policy == 'delivery'` (barang fisik yang ditagih
setelah pengiriman — sangat umum), kolom **Amount To Invoice** di Sales Analysis melaporkan
seluruh nilai order sejak SO dikonfirmasi, bukan hanya bagian yang sudah bisa ditagih. Untuk
produk ber-pajak `price_include`, subtotal yang dipakai juga sudah termasuk pajak alih-alih
`total_excluded`. Keduanya membuat metrik utama modul ini overstated.
**Rekomendasi:** pakai variabel lokal `price_subtotal` di cabang `else` (konsisten dengan core dan
dengan cabang `if` di method yang sama):
`amount_to_invoice = price_subtotal - (line.waiting_for_payment + line.amount_received)`.
**Keputusan pemilik modul:** *(kosong — diisi manusia)*

---

### F-18 — Modul tidak punya bundle `assets`, sehingga tidak bisa menampung test Tour
**Tag:** `[PERLU-KEPUTUSAN]` · **Prioritas:** Rendah · **Ditemukan:** Step 07
**Lokasi:** `advanced_sales_analysis/__manifest__.py`
**Deskripsi:** Manifest tidak punya key `assets` sama sekali. Konsekuensinya, modul ini tidak
punya jalur resmi untuk memuat file JS apa pun — termasuk file Tour test
(`static/tests/tours/*.js`), yang harus terdaftar di bundle `web.assets_tests` supaya
`HttpCase.start_tour()` bisa menemukannya.
**Dampak:** bukan bug fungsional — modul ini memang tidak punya JS produksi, jadi tidak ada yang
hilang saat runtime. Yang terdampak adalah kemampuan MENGUJI-nya: siapa pun yang nanti ingin
menambah Tour test (jalur standar Odoo untuk regression test UI) harus lebih dulu menambah key
`assets` ke manifest. BACKFILL tidak melakukannya karena di luar mandat "hanya menambah file
test" — Step 07 memakai `HttpCase.browser_js()` sebagai gantinya, yang memberi bukti setara tanpa
menyentuh manifest (lihat `test/07_QA_TESTING.md` §2).
**Rekomendasi:** kalau ke depan modul ini mau punya Tour test, tambahkan ke manifest:
```python
'assets': {
    'web.assets_tests': ['advanced_sales_analysis/static/tests/tours/*.js'],
},
```
Bundle `web.assets_tests` hanya dimuat dalam mode test — tidak menambah beban asset di produksi.
**Keputusan pemilik modul:** *(kosong — diisi manusia)*

---

### F-19 — `_select_sale()` override gagal di Odoo 17 patch tertentu — UNION column mismatch
**Tag:** `[PERLU-KEPUTUSAN]` · **Prioritas:** Tinggi
**Lokasi:** `advanced_sales_analysis/models/sale_report.py:19-26`
**Ref:** F-08, BR-01
**Ditemukan:** post-backfill, saat deploy ke production `demo17.doodex.net` (2026-08-20)
**Deskripsi:** Pada Odoo 17 patch tertentu (termasuk instalasi production Doodex), `sale.report._query()`
mengandung UNION ALL dua SELECT: SELECT pertama untuk baris SO biasa (dibangun lewat `_select_sale()`),
SELECT kedua untuk baris section/separator tanpa produk (hardcoded, dimulai dengan `-MIN(l.id) AS id`).
Modul meng-override `_select_sale()` dan menambahkan 3 kolom baru hanya ke SELECT pertama. SELECT kedua
tidak diperbarui → UNION dua cabang punya jumlah kolom berbeda → PostgreSQL error saat view di-query:

```
psycopg2.errors.SyntaxError: each UNION query must have the same number of columns
LINE 113:             -MIN(l.id) AS id,
```

Error ini muncul setiap kali user membuka **Sales → Reporting → Sales** (pivot Sales Analysis) —
laporan tidak bisa dibuka sama sekali.

**Kenapa tidak tertangkap di backfill:** Docker image `odoo:17.0` yang dipakai testing (2026-08-18)
menggunakan patch yang berbeda dari instalasi production. Pada versi Docker, UNION ALL di `_query()`
tidak ada atau strukturnya kompatibel — semua 37 test lulus. Pada production, UNION sudah ada dan
menyebabkan mismatch. Ini pola version drift yang berulang saat addon dikembangkan di image publik
tapi di-deploy ke instalasi yang sudah di-patch lebih lanjut.

**Relasi ke F-08:** F-08 sudah mencatat bahwa hook resmi `_select_additional_fields()` tidak dipakai.
Jika modul memakai `_select_additional_fields()` sejak awal, Odoo secara otomatis akan memasukkan
field baru ke SELECT yang relevan (termasuk menangani kasus UNION dengan benar sesuai implementasi
core). Override `_select_sale()` dengan string concatenation melewati mekanisme ini.

**Dampak:** laporan Sales Analysis tidak bisa dibuka di production — feature utama modul ini tidak
berfungsi. Ini blocker deployment.

**Rekomendasi:** pindahkan ketiga kolom ke `_select_additional_fields()` (sesuai rekomendasi F-08),
ATAU override `_query()` secara penuh dan tambahkan `0 AS amount_received, 0 AS waiting_for_payment,
0 AS amount_to_invoice` ke SELECT kedua UNION. Solusi `_select_additional_fields()` lebih tahan patch
karena mengikuti API resmi core.

**Keputusan pemilik modul:** *(kosong — diisi manusia)*

---

## Limitasi Tool

Gap yang genuinely tidak bisa ditutup tanpa mengubah kode bisnis atau menambah infrastruktur di
luar scope — dicatat apa adanya, tidak dipaksa "selesai":

1. **Dampak akhir F-01 ke portal pembayaran `account_payment` tidak diverifikasi end-to-end.**
   Membuktikannya butuh `payment_provider` aktif + `payment.transaction` sungguhan. Yang sudah
   terbukti lewat eksekusi: definisi DAN semantik field core benar-benar tergantikan. Dampak
   turunannya ke UI portal disimpulkan dari membaca `account_payment/models/account_move.py`, dan
   ditandai sebagai kesimpulan-dari-baca-kode, bukan hasil eksekusi.
2. **Kekhawatiran performa F-15 tidak diukur.** `search()` di dalam loop bersarang baru terasa di
   database berukuran produksi; database test terlalu kecil untuk memberi angka yang berarti.
   Mengukurnya butuh dataset produksi (atau generator data skala besar) yang di luar scope sesi
   ini. Tidak ada klaim performa yang dibuat di dokumen mana pun.
3. **F-13 di `account.payment`/`account.bank.statement.line` tidak diverifikasi lewat UI.** Bukti
   perembetannya berasal dari WARNING instalasi Odoo, bukan dari membuka form kedua model itu.

Tidak ada gap yang butuh instrumentasi/logging tambahan ke kode bisnis — semua temuan di atas bisa
dibuktikan (atau eksplisit tidak dibuktikan) tanpa menyentuh `models/`.
