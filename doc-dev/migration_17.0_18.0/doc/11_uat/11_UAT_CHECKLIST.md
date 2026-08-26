# UAT Checklist — Migrasi advanced_sales_analysis

**Step:** 11 — UAT Sign-off (final)
**Ref:** `05_acceptance/05a_MIGRATION_ACCEPTANCE_CRITERIA.md`, `10_qa/10_BUSINESS_FLOW_MIGRATION.md`
**Tanggal:** 2026-08-21

> Kriteria sukses: user TIDAK merasakan bedanya dibanding versi lama, KECUALI dua hal yang memang disepakati berubah (lihat "Review Item Out-of-Scope" di bawah).
>
> **Dokumen ini adalah draft test script — dijalankan sendiri oleh business user/stakeholder, bukan oleh AI/developer.** Kolom Actual dan Status dikosongkan sengaja.

---

## Persiapan Sebelum UAT (Precondition & Data)

- [ ] Modul "Advanced Sales Analysis" versi 18.0.1.0.0 sudah terinstall di environment UAT.
- [ ] Login sebagai user dengan role Sales/Finance (bukan cuma Administrator) — supaya UAT juga memvalidasi hak akses standar.
- [ ] Minimal 1 produk yang bisa dijual sudah ada (apa saja, harga berapa saja).
- [ ] Minimal 1 pelanggan (contact) sudah ada.
- [ ] Sebaiknya dijalankan di **database staging/salinan**, bukan database produksi asli.

## Skenario Test (Test Script)

### T-01: Melihat metrik keuangan baru di laporan Sales Analysis

**Data dummy yang perlu dientri:** Sale Order baru, pelanggan mana saja, satu baris produk apa saja, harga jual **100**, tanpa diskon.

| # | Langkah | Expected | Actual | Status |
|---|---|---|---|---|
| 1 | Buat Sale Order dengan data di atas, klik "Confirm". | Order berhasil dikonfirmasi. | | [ ] Pass [ ] Fail |
| 2 | Klik "Create Invoice" → "Regular Invoice" → "Create Draft Invoice". | Invoice draft terbuat. | | [ ] Pass [ ] Fail |
| 3 | Buka invoice, klik "Confirm" (post). | Invoice terkonfirmasi/posted. | | [ ] Pass [ ] Fail |
| 4 | Klik "Register Payment", isi jumlah **100**, klik "Create Payment". | Invoice berstatus "Paid". | | [ ] Pass [ ] Fail |
| 5 | Buka menu Sales → Reporting → Sales. | Laporan pivot terbuka, tidak ada halaman error. | | [ ] Pass [ ] Fail |
| 6 | Klik dropdown "Measures", cari dan aktifkan: "Amount Received", "Waiting for Payment", "Amount To Invoice". | Ketiga measure muncul di daftar dan bisa dipilih. | | [ ] Pass [ ] Fail |
| 7 | Cari baris untuk order dari langkah 1. | "Amount Received" = 100, "Waiting for Payment" = 0, "Amount To Invoice" = 0. | | [ ] Pass [ ] Fail |

### T-02: Order dengan uang muka (down payment) tetap terhitung masuk akal

**Data dummy yang perlu dientri:** Sale Order baru, harga jual **200**, pakai fitur "Down Payment" saat membuat invoice pertama (invoice sebagian dulu sebagai uang muka, mis. 50).

| # | Langkah | Expected | Actual | Status |
|---|---|---|---|---|
| 1 | Buat & konfirmasi Sale Order 200. | Order confirmed. | | [ ] Pass [ ] Fail |
| 2 | "Create Invoice" → pilih "Down payment" → isi jumlah 50 → buat invoice. | Invoice uang muka 50 terbuat. | | [ ] Pass [ ] Fail |
| 3 | Post invoice, register payment penuh (50). | Invoice DP lunas. | | [ ] Pass [ ] Fail |
| 4 | Buka Sales Analysis, tambahkan 3 measure yang sama seperti T-01. | Angka untuk order ini muncul dan terlihat wajar (uang muka tercermin sebagai bagian yang sudah diterima) — TIDAK boleh menampilkan angka yang jelas rusak (kosong/negatif ekstrem tanpa penjelasan). | | [ ] Pass [ ] Fail |

### T-03: Pembayaran sebagian (partial payment) terhitung terpisah dari yang belum ditagih

**Data dummy yang perlu dientri:** Sale Order 100, invoice penuh, bayar cuma **60** dari 100.

| # | Langkah | Expected | Actual | Status |
|---|---|---|---|---|
| 1 | Buat, konfirmasi, invoice, post — bayar 60 saja (bukan 100). | Invoice berstatus "Partially Paid". | | [ ] Pass [ ] Fail |
| 2 | Buka Sales Analysis, cek measure untuk order ini. | "Amount Received" = 60, "Waiting for Payment" = 40 (sisa yang sudah ditagih tapi belum dibayar). | | [ ] Pass [ ] Fail |

### T-04: Fitur lain yang berhubungan dengan "sisa yang belum ditagih" tetap normal

> Skenario ini khusus mengecek dampak dari satu perbaikan teknis migrasi (lihat "Review Item Out-of-Scope") — pastikan fitur CORE Odoo (bukan buatan modul ini) yang memakai informasi "sisa belum ditagih" tetap berfungsi wajar.

**Data dummy yang perlu dientri:** Kalau perusahaan Anda memakai fitur **Credit Limit** pelanggan (Settings → Invoicing/Accounting → cek apakah "Credit Limit" aktif) — pakai pelanggan yang punya Credit Limit diisi. Kalau TIDAK memakai fitur ini, skenario ini cukup langkah 1-2 saja.

| # | Langkah | Expected | Actual | Status |
|---|---|---|---|---|
| 1 | Buka form Sale Order apa pun yang masih ada sisa tagihan. | Form terbuka normal, tidak ada field yang kosong/error terkait jumlah yang belum ditagih. | | [ ] Pass [ ] Fail |
| 2 | Buka form pelanggan (Customer) terkait, cek info "amount to invoice"/statistik terkait kalau ada di layout. | Angka masuk akal, tidak error. | | [ ] Pass [ ] Fail |
| 3 | *(Kalau pakai Credit Limit)* Buat invoice yang membuat total tagihan pelanggan melebihi Credit Limit-nya, coba konfirmasi. | Warning credit limit muncul (atau tidak, sesuai konfigurasi perusahaan) dengan angka yang masuk akal — bukan error Python atau angka yang jelas salah. | | [ ] Pass [ ] Fail |

### T-05: Item yang TIDAK Bisa/TIDAK Perlu Dites Lewat Tampilan Biasa (Informasi, Bukan Kegagalan)

- **Produk yang ditagih berdasarkan pengiriman (invoice policy "Delivered quantities"):** kalau Anda memesan produk seperti ini dan baru mengirim sebagian, kolom **"Amount To Invoice"** akan menampilkan nilai TOTAL order (bukan cuma bagian yang sudah bisa ditagih sesuai pengiriman). **Ini bukan bug baru** — perilaku ini sudah ada sejak versi sebelumnya dan sengaja dipertahankan sesuai keputusan migrasi. Kalau Anda melihat ini, tidak perlu dilaporkan sebagai kegagalan test.
- **Order dalam mata uang asing:** kolom 3 measure baru tidak dikonversi ke mata uang perusahaan (beda dari kolom "Total" biasa yang sudah dikonversi) — juga perilaku lama yang dipertahankan, bukan temuan baru.

## Sign-off per Kelompok Fitur

> **CATATAN TRANSPARANSI (2026-08-21):** T-01 s/d T-04 di bawah TIDAK dieksekusi manual lewat UI oleh business user — pemilik project ("Kuncoro", *"UAT dianggap selesai, percaya pada ai test"*) memutuskan menerima hasil test otomatis AI sebagai basis sign-off, menggantikan eksekusi tangan sendiri yang jadi prinsip default dokumen ini (lihat catatan di §atas). Kolom "Status" di bawah diisi berdasarkan **kesetaraan cakupan** ke test otomatis yang SUDAH dijalankan nyata (Step 9: 38/38 unit/integration test pass; Step 10: verifikasi `odoo shell` langsung untuk MF-02) — BUKAN laporan "sudah dicoba di UI dan sukses". Risiko yang TIDAK tertutup oleh basis ini: bug spesifik-UI (rendering, label, klik tombol) yang secara desain tidak bisa ditangkap test level Python/data — lihat `10_qa/human_qa/` kalau ingin menutup gap ini nanti.

| # | Kelompok fitur | Skenario tercakup | Status | Catatan |
|---|---|---|---|---|
| 1 | Metrik dasar Sales Analysis | T-01 | [x] Pass (basis: test otomatis) | Setara `test_ac_07_01*` (Step 9) — nilai `amount_received`/`waiting_for_payment`/`amount_to_invoice` dikonfirmasi benar di level data, bukan diklik manual di pivot. |
| 2 | Uang muka & pembayaran sebagian | T-02, T-03 | [x] Pass (basis: test otomatis) | Setara `test_ac_03_*`/`test_ac_04_*`/`test_ac_05_*` (Step 9). |
| 3 | Kompatibilitas dengan fitur core (credit limit dsb) | T-04 | [x] Pass (basis: test otomatis + odoo shell) | Bagian data/ORM dikonfirmasi langsung (Step 10, `odoo shell` — field core tidak lagi collide). Bagian UI (warning credit limit ASLI tampil di layar) **tidak pernah diverifikasi visual sama sekali** — risiko residual terbesar dari keputusan ini. |

## Review Item Out-of-Scope

Stakeholder mengonfirmasi sadar & menerima dua perubahan yang disengaja dari proses migrasi ini (bukan bug, keputusan yang sudah diambil pemilik modul — lihat `FINDINGS.md` untuk detail teknis lengkap):

- **Granularitas laporan Sales Analysis berubah (MF-01):** untuk order dengan >1 baris produk sama tapi harga satuan berbeda, laporan 18.0 akan menampilkan LEBIH BANYAK baris dibanding versi 17.0 (bukan data hilang, cuma disajikan lebih detail) — ini perubahan dari Odoo sendiri, sudah disetujui diterima apa adanya.
- **Nama field teknis `amount_to_invoice` diganti jadi `asa_amount_to_invoice` di balik layar (MF-02):** untuk menghindari bentrok dengan fitur baru Odoo 18 (terkait Credit Limit). Perubahan ini TIDAK terlihat di UI — nama measure "Amount To Invoice" yang Anda lihat di laporan tetap sama.
- 15 catatan perilaku lama (bug/quirk) yang sudah ada sejak versi sebelumnya (lihat T-05 di atas untuk 2 contoh paling relevan ke UAT) — SEMUA sengaja dipertahankan identik, bukan diperbaiki saat migrasi ini, kecuali pemilik modul memutuskan lain di kemudian hari.

## Prasyarat Sebelum Go-Live Produksi

- [ ] **Rehearsal upgrade sungguhan belum dilakukan** — project ini sifatnya "port kode saja" (instalasi baru, bukan upgrade instance dengan data produksi lama). Kalau modul ini akan dipasang di instance yang SUDAH punya data produksi (bukan instalasi baru), lakukan rehearsal upgrade (clone data produksi → install modul → spot-check data) SEBELUM go-live — ini belum tercakup di project migrasi ini karena scope awal disepakati "port kode saja".
- [ ] Backup database produksi sebelum instalasi/upgrade nyata.
- [ ] Jalankan `10_qa/human_qa/` (kalau belum) sebagai polish akhir sebelum go-live.

## Sign-off

| Role | Nama | Tanggal | Tanda tangan |
|---|---|---|---|
| PM | | | |
| FA | | | |
| User/Project Owner | Kuncoro | 2026-08-21 | *(disetujui via chat — "UAT dianggap selesai, percaya pada ai test", bukan tanda tangan fisik/digital formal)* |

> **PENYIMPANGAN DARI PRINSIP DOKUMEN INI (dicatat eksplisit, bukan disembunyikan):** baris "User/Project Owner" di atas diisi AI atas instruksi eksplisit pemilik project SAAT ITU JUGA di chat, TANPA eksekusi tangan sendiri atas skenario T-01 s/d T-04 — bertentangan dengan prinsip di bagian atas dokumen ini ("sign-off idealnya tetap didasarkan pada eksekusi tangan sendiri, bukan laporan AI"). Baris PM/FA tetap dikosongkan (belum ada instruksi serupa dari role tersebut). Risiko yang diterima pemilik project dengan keputusan ini: gap visual/UI (lihat catatan di §Sign-off per Kelompok Fitur) tidak pernah terverifikasi sama sekali sebelum go-live.
