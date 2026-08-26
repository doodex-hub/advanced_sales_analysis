# UAT Checklist — Migrasi advanced_sales_analysis

**Step:** 11 — UAT Sign-off (final)
**Ref:** `05_acceptance/05a_MIGRATION_ACCEPTANCE_CRITERIA.md`, `10_qa/10_BUSINESS_FLOW_MIGRATION.md`
**Tanggal:** 2026-08-26

> Kriteria sukses: user TIDAK merasakan bedanya dibanding versi 18.0, kecuali item yang memang disepakati berubah (lihat "Review Item Out-of-Scope" di bawah).
>
> Dokumen ini adalah draft test script siap pakai untuk dijalankan sendiri oleh business user/stakeholder — kolom Actual/Status/Sign-off DIKOSONGKAN oleh AI, diisi oleh yang benar-benar menjalankan.

---

## Persiapan Sebelum UAT (Precondition & Data)

- [ ] Modul `advanced_sales_analysis` versi `19.0.1.0.0` sudah terinstall dan bisa diakses di instance Odoo 19.0 (staging, bukan produksi).
- [ ] Login sebagai user dengan role Sales/Finance (bukan cuma Administrator) — supaya UAT juga memvalidasi hak akses standar untuk melihat laporan Sales Analysis.
- [ ] Minimal satu produk (apa saja, harga bebas) dan satu kontak/customer sudah tersedia untuk dipakai membuat Sale Order dummy.
- [ ] Minimal satu produk lain yang punya PAJAK terpasang (berapa pun persennya) — dipakai di T-03 untuk memastikan perubahan teknis di balik layar (migrasi ke Odoo 19) tidak mengganggu perhitungan.
- [ ] Database yang dipakai UAT sebaiknya salinan/staging, bukan database produksi asli.

## Skenario Test (Test Script)

### T-01: Buka laporan Sales Analysis dan lihat tiga kolom baru

**Data dummy yang perlu dientri:** Tidak ada data baru — cukup pakai data yang sudah ada di sistem (atau data dummy dari persiapan di atas).

| # | Langkah | Expected | Actual | Status |
|---|---|---|---|---|
| 1 | Buka menu **Sales → Reporting → Sales** | Laporan pivot terbuka normal, tidak ada halaman error | | [ ] Pass [ ] Fail |
| 2 | Klik dropdown **Measures** di pojok kanan atas tabel | Muncul daftar measure, termasuk **Amount Received**, **Waiting for Payment**, **Amount To Invoice** | | [ ] Pass [ ] Fail |
| 3 | Klik ketiga measure itu satu-satu untuk mengaktifkannya | Kolom baru muncul di tabel, ada isinya (bukan error/kosong semua) | | [ ] Pass [ ] Fail |

### T-02: Buat order, tagih, dan bayar — cek angka tiga measure cocok

**Data dummy yang perlu dientri:** Sale Order baru, satu baris produk, harga **100**, tanpa pajak, ke customer manapun.

| # | Langkah | Expected | Actual | Status |
|---|---|---|---|---|
| 1 | Buat Sale Order baru, satu baris produk harga 100, klik **Confirm** | Order berhasil terkonfirmasi | | [ ] Pass [ ] Fail |
| 2 | Klik **Create Invoice** → **Regular Invoice** → **Create and View Invoice** | Invoice terbentuk, dalam status draft | | [ ] Pass [ ] Fail |
| 3 | Klik **Confirm** di invoice (untuk post) | Invoice ter-post, tidak ada error | | [ ] Pass [ ] Fail |
| 4 | Klik **Register Payment**, isi 100, klik **Create Payment** | Pembayaran tercatat, status invoice jadi "Paid" | | [ ] Pass [ ] Fail |
| 5 | Buka **Sales → Reporting → Sales**, cari baris order ini, lihat 3 measure baru | **Amount Received = 100**, **Waiting for Payment = 0**, **Amount To Invoice = 0** | | [ ] Pass [ ] Fail |

### T-03: Order dengan produk berpajak — pastikan tidak ada error tersembunyi

**Data dummy yang perlu dientri:** Sale Order baru, satu baris pakai produk yang PUNYA PAJAK (dari persiapan di atas), harga bebas, JANGAN difakturkan (biarkan status "belum ditagih").

| # | Langkah | Expected | Actual | Status |
|---|---|---|---|---|
| 1 | Buat Sale Order dengan produk berpajak, klik **Confirm** | Order berhasil terkonfirmasi, **tidak ada pesan error apa pun muncul di layar** | | [ ] Pass [ ] Fail |
| 2 | Buka **Sales → Reporting → Sales**, cari baris order ini, aktifkan measure **Amount To Invoice** | Kolom terisi angka (bukan kosong/simbol error) | | [ ] Pass [ ] Fail |

> **Kenapa T-03 penting khusus untuk migrasi ini:** perubahan teknis di balik layar migrasi ke Odoo 19.0 menyentuh cara sistem membaca informasi pajak di baris order — kalau ada yang terlewat, gejalanya justru muncul PALING JELAS di skenario order-berpajak seperti ini (halaman error/gagal simpan), bukan di order tanpa pajak seperti T-02.

### T-04: Item yang TIDAK Bisa Dites Lewat Tampilan Biasa (Informasi, Bukan Kegagalan)

- **Perilaku laporan dengan Point of Sale (POS) terinstall bersamaan** — belum ada environment UAT dengan modul POS aktif untuk mengonfirmasi laporan gabungan Sales+POS tetap normal. Ini gap yang sudah diketahui sejak migrasi sebelumnya (17→18), bukan sesuatu yang baru rusak di migrasi ini — kalau instance produksi memakai POS, sebutkan ke tim dev supaya bisa diuji terpisah sebelum go-live.
- **Baris uang muka (Down Payment) dan order multi-currency** menghasilkan angka yang SENGAJA tidak sepenuhnya "rapi" (dua bug lama yang dipertahankan apa adanya, bukan diperbaiki di migrasi ini) — kalau user melihat sesuatu yang terasa aneh di dua skenario itu, itu bukan regresi migrasi, cukup dikonfirmasi masih sama seperti sebelumnya (lihat `human_qa/03_DETAIL.md` untuk detail teknis kalau perlu).

## Sign-off per Kelompok Fitur

> **CATATAN TRANSPARANSI (2026-08-26):** T-01 s/d T-03 di bawah TIDAK dieksekusi manual lewat UI oleh business user — pemilik project ("Kuncoro", *"UAT anggap selesai, percaya pada ai test"*) memutuskan menerima hasil test otomatis AI sebagai basis sign-off, menggantikan eksekusi tangan sendiri yang jadi prinsip default dokumen ini (lihat catatan di §atas). Kolom "Status" di bawah diisi berdasarkan **kesetaraan cakupan** ke test otomatis yang SUDAH dijalankan nyata (Step 6/9: G1, `0 failed, 0 error(s) of 39 tests`, termasuk `test_qa_measures_baru_tersedia_di_pivot_sales_analysis` via Chrome headless ASLI dan `test_ac_06_03b_tax_ids_rename_price_include` yang memverifikasi fix DIFF-01) — BUKAN laporan "sudah dicoba di UI dan sukses" oleh manusia. Risiko yang TIDAK tertutup oleh basis ini: bug spesifik-UI (rendering, label, klik tombol) yang secara desain tidak bisa ditangkap test level Python/data — lihat `10_qa/human_qa/` kalau ingin menutup gap ini nanti.

| # | Kelompok fitur | Skenario tercakup | Status | Catatan |
|---|---|---|---|---|
| 1 | Instalasi bersih & laporan terbuka | T-01 | [x] Pass (basis: test otomatis) | Setara `test_qa_measures_baru_tersedia_di_pivot_sales_analysis` (Step 6/9) — Chrome headless ASLI mengonfirmasi pivot terbuka dan measure muncul, bagian dari 39/39 test G1. |
| 2 | Metrik finansial pivot (angka cocok) | T-02 | [x] Pass (basis: test otomatis) | Setara `test_ac_04_*`/`test_ac_05_*`/`test_ac_06_*`/`test_ac_07_*` (Step 9) — nilai `amount_received`/`waiting_for_payment`/`amount_to_invoice` dikonfirmasi benar di level data, bukan diklik manual di pivot. |
| 3 | Order berpajak tidak error (verifikasi migrasi 19.0) | T-03 | [x] Pass (basis: test otomatis) | Setara `test_ac_06_03b_tax_ids_rename_price_include` (Step 6/9) — memverifikasi LANGSUNG fix DIFF-01 (`tax_id`→`tax_ids`) di level kode, hasil numerik benar. Bagian visual (tidak ada error di LAYAR saat user klik) tidak pernah diverifikasi manual. |

## Review Item Out-of-Scope

Stakeholder mengonfirmasi sadar & menerima hal-hal berikut (bukan bug baru, sudah disetujui sebelumnya):

- Laporan Sales Analysis di Odoo 19.0 bisa menampilkan LEBIH BANYAK baris untuk order dengan kombinasi harga/status tertentu dibanding sebelumnya — ini perubahan dari Odoo sendiri (bukan dari modul ini), sudah disetujui pemilik modul saat migrasi 17→18 dan tidak berubah lagi di migrasi 18→19 ini.
- Perhitungan uang muka dan order multi-currency di tiga measure baru punya keterbatasan lama yang sengaja tidak diperbaiki (lihat T-04 di atas).

## Prasyarat Sebelum Go-Live Produksi

- [ ] Rehearsal upgrade sungguhan (kalau ini akan diterapkan ke instance produksi dengan data asli, bukan instalasi baru) — **belum dilakukan di project ini**, karena disepakati sifatnya "port kode saja" (`01a_MIGRATION_INTAKE.md` §3). Kalau rencana berubah jadi upgrade instance produksi, lakukan rehearsal terpisah sebelum go-live.
- [ ] Backup database produksi sebelum upgrade nyata (kalau berlaku).

## Sign-off

| Role | Nama | Tanggal | Tanda tangan |
|---|---|---|---|
| PM | | | |
| FA | | | |
| User/Project Owner | Kuncoro | 2026-08-26 | *(disetujui via chat — "UAT anggap selesai, percaya pada ai test", bukan tanda tangan fisik/digital formal)* |

> **PENYIMPANGAN DARI PRINSIP DOKUMEN INI (dicatat eksplisit, bukan disembunyikan):** baris "User/Project Owner" di atas diisi AI atas instruksi eksplisit pemilik project SAAT ITU JUGA di chat, TANPA eksekusi tangan sendiri atas skenario T-01 s/d T-03 — bertentangan dengan prinsip di bagian atas dokumen ini ("sign-off idealnya tetap didasarkan pada eksekusi tangan sendiri, bukan laporan AI"). Baris PM/FA tetap dikosongkan (belum ada instruksi serupa dari role tersebut). Risiko yang diterima pemilik project dengan keputusan ini: gap visual/UI (lihat catatan di §Sign-off per Kelompok Fitur) tidak pernah terverifikasi sama sekali sebelum go-live — sama seperti keputusan yang diambil pada migrasi 17→18 modul ini sebelumnya.
