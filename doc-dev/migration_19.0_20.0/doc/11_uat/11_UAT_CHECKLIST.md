# UAT Checklist — Migrasi advanced_sales_analysis

**Step:** 11 — UAT Sign-off (final)
**Versi:** 19.0 → 20.0
**Ref:** `05_acceptance/05a_MIGRATION_ACCEPTANCE_CRITERIA.md`, `10_qa/10_BUSINESS_FLOW_MIGRATION.md`
**Tanggal:** 2026-09-24
**Status:** ✔️ Disetujui 2026-09-24 — sign-off berbasis **bukti test AI** atas keputusan eksplisit pemilik project (Kuncoro: *"UAT sign-off pakai bukti test AI, tutup migrasinya"*). Kolom Actual T-01…T-03 TIDAK diisi (tidak ada eksekusi tangan manusia) — lihat catatan penyimpangan di §Sign-off.

> Bukti AI yang sudah ada (bukan pengganti UAT): Step 9 (41 method test, 0 failed di 3 environment) dan Step 10 (6/6 skenario, A/B 19.0↔20.0 identik). Di migrasi 18→19 dev memilih sign-off berbasis bukti AI sebagai penyimpangan eksplisit — itu keputusan per project dan **tidak diasumsikan** — pemilik project memutuskan ulang secara eksplisit untuk migrasi 19→20 pada 2026-09-24 (lihat §Sign-off).

---

## Persiapan Sebelum UAT

- [ ] Instance Odoo 20.0 (staging/salinan, BUKAN produksi) dengan `advanced_sales_analysis` 20.0.1.0.0 terinstall. Untuk uji cepat lokal: server G2 AI di `http://localhost:8080` (DB `advanced_sales_analysis_test_20`, data QA "QA20 Customer" sudah ada).
- [ ] Login sebagai user Sales Manager + Accounting (bukan hanya Administrator).
- [ ] Data: 1 customer, 2 produk layanan tanpa pajak (harga 1000 dan 500, invoicing policy "Ordered quantities"), jurnal bank untuk Register Payment.

## Skenario Test

### T-01: Sales Analysis terbuka & 3 measure tersedia
**Data dummy:** —

| # | Langkah | Expected | Actual | Status |
|---|---|---|---|---|
| 1 | Sales → Reporting → Sales → view Pivot | Pivot terbuka tanpa error | | [ ] Pass [ ] Fail |
| 2 | Measures → centang Amount Received, Waiting for Payment, Amount To Invoice | 3 kolom tampil, tidak ada pesan error server | | [ ] Pass [ ] Fail |

### T-02: Uang masuk / menunggu bayar / belum ditagih
**Data dummy:** SO A 1×1000 (fakturkan, bayar penuh); SO B 1×500 (fakturkan, bayar 200); SO C 1×1000 + 1×500 (confirm saja)

| # | Langkah | Expected | Actual | Status |
|---|---|---|---|---|
| 1 | Buat & proses SO A, B, C seperti di atas | Semua tersimpan tanpa error | | [ ] Pass [ ] Fail |
| 2 | Pivot, baris = Order Reference | A: 1000/0/0 · B: 200/300/0 · C: 0/0/1500 (Received/Waiting/To Invoice) | | [ ] Pass [ ] Fail |
| 3 | Total pivot | 1200 / 300 / 1500 | | [ ] Pass [ ] Fail |

### T-03: Uang muka & credit note
**Data dummy:** SO 1000 → faktur Down payment 30% (belum dibayar); lalu bayar faktur DP; lalu buat credit note

| # | Langkah | Expected | Actual | Status |
|---|---|---|---|---|
| 1 | Faktur DP 30% di-confirm, belum dibayar; catat Received/Waiting/To Invoice di pivot | Identik dengan hasil skenario yang sama di 19.0 | | [ ] Pass [ ] Fail |
| 2 | Bayar faktur DP penuh; catat lagi | Identik 19.0 | | [ ] Pass [ ] Fail |
| 3 | Buat credit note untuk faktur DP; catat lagi | Identik 19.0 | | [ ] Pass [ ] Fail |

> Catatan: T-03 tidak dieksekusi end-to-end lewat UI oleh AI (alur wizard down payment). Logic DP diuji test otomatis AC-03/AC-04-06 dengan faktur yang dibuat langsung. Karena itu expected ditulis "identik 19.0", bukan angka referensi.

### T-XX: Item yang TIDAK bisa dites lewat tampilan biasa (informasi)
- Kolisi `amount_paid` dengan `account_payment` (BSL-006) — internal ORM, diverifikasi test otomatis.
- Granularitas baris per deskripsi (MF-03) — hanya terlihat di list view laporan tanpa group-by.
- Nilai baris POS (MF-02) — hanya kalau Point of Sale dipakai.

## Sign-off per Kelompok Fitur

| # | Kelompok fitur | Skenario tercakup | Status | Catatan |
|---|---|---|---|---|
| 1 | Sales Analysis 3 measure | T-01, T-02 | [x] Pass (basis: bukti test AI) | T-01 setara `test_qa_measures_baru_tersedia_di_pivot_sales_analysis` (Chrome headless asli, Run A/B/C). T-02 setara QA Step 10 S-02: skenario yang sama dijalankan live di 19.0 dan 20.0, hasil identik (1200/300/1500) + AC-04/05/06/07. Tidak diklik manual di pivot. |
| 2 | Uang muka & credit note | T-03 | [x] Pass (basis: bukti test AI) | Setara `test_ac_03_*`, `test_ac_04_05/06`, `test_ac_02_02` (faktur dibuat langsung, bukan lewat wizard down payment UI). Alur wizard DP end-to-end di UI 20.0 TIDAK pernah dieksekusi. |

## Review Item Out-of-Scope / Perubahan Diterima

Stakeholder mengonfirmasi sadar & menerima:
- [x] MF-02 — dengan Point of Sale terinstall, *Amount To Invoice* di baris POS berisi subtotal POS belum difakturkan (19.0: kosong). Diputuskan dev 2026-09-24.
- [x] MF-03 — baris laporan dipisah per deskripsi baris SO (perubahan core Odoo 20). Total tidak berubah. Diterima pemilik project saat sign-off 2026-09-24 (sebelumnya diputuskan AI mengikuti preseden MF-01 17→18).
- [x] Aset store (banner.gif, icon.png, index.html) diambil dari branch rilis `19.0`.
- [x] 15 quirk lama (BSL-011…BSL-021: deteksi "Down payment" by nama, kolom tanpa konversi kurs, label field duplikat, dst.) sengaja TIDAK diperbaiki.

## Prasyarat Sebelum Go-Live Produksi

- [ ] Migrasi = port kode (instalasi baru). Kalau ternyata produksi 19.0 akan di-upgrade in-place, Step 7 (data migration) harus dibuka lagi — belum dikerjakan.
- [ ] Backup database produksi sebelum deploy.
- [ ] Postgres produksi ≥ 16 (Odoo 20 memberi warning di Postgres 15).
- [ ] README modul sudah direview — tidak menyebut versi Odoo (dicek A6).
- [ ] `git push` branch `migration/20.0` & merge — keputusan/aksi dev.

## Sign-off

| Role | Nama | Tanggal | Tanda tangan |
|---|---|---|---|
| PM | | | |
| FA | | | |
| User/Project Owner | Kuncoro | 2026-09-24 | *(disetujui via chat — "UAT sign-off pakai bukti test AI, tutup migrasinya", bukan tanda tangan fisik/digital formal)* |

> **PENYIMPANGAN DARI PRINSIP DOKUMEN INI (dicatat eksplisit):** baris "User/Project Owner" diisi AI atas instruksi eksplisit pemilik project di chat, TANPA eksekusi tangan sendiri atas T-01…T-03. Baris PM/FA dikosongkan (tidak ada instruksi dari role tersebut). Pola yang sama dengan migrasi 17→18 dan 18→19 modul ini. **Risiko sisa yang diterima:** (1) perilaku visual/UI di luar yang dicek `browser_js` (label, rendering, klik lain) tidak diverifikasi manusia; (2) alur wizard down payment UI 20.0 end-to-end tidak dieksekusi; (3) nilai baris POS MF-02 hanya dari baca kode (tidak ada POS order dibuat). Checklist `10_qa/human_qa/` tersedia untuk menutup gap ini kapan saja.

## Penutupan Migrasi

- [x] `doc/MIGRATION_CLOSED.md` ditulis (2026-09-24) — SHA = commit "Step 11 gate passed" di `migration/20.0`.
