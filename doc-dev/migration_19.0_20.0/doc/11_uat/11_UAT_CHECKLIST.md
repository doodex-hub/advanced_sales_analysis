# UAT Checklist — Migrasi advanced_sales_analysis

**Step:** 11 — UAT Sign-off (final)
**Versi:** 19.0 → 20.0
**Ref:** `05_acceptance/05a_MIGRATION_ACCEPTANCE_CRITERIA.md`, `10_qa/10_BUSINESS_FLOW_MIGRATION.md`
**Tanggal:** 2026-09-24
**Status:** 🔄 Draft siap dieksekusi — **menunggu eksekusi & sign-off manusia** (PM/FA/User). AI tidak mengisi kolom Actual/Status/Sign-off.

> Bukti AI yang sudah ada (bukan pengganti UAT): Step 9 (41 method test, 0 failed di 3 environment) dan Step 10 (6/6 skenario, A/B 19.0↔20.0 identik). Di migrasi 18→19 dev memilih sign-off berbasis bukti AI sebagai penyimpangan eksplisit — itu keputusan per project dan **tidak diasumsikan berlaku lagi di sini**.

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
| 1 | Sales Analysis 3 measure | T-01, T-02 | [ ] Pass [ ] Fail | |
| 2 | Uang muka & credit note | T-03 | [ ] Pass [ ] Fail | |

## Review Item Out-of-Scope / Perubahan Diterima

Stakeholder mengonfirmasi sadar & menerima:
- [ ] MF-02 — dengan Point of Sale terinstall, *Amount To Invoice* di baris POS berisi subtotal POS belum difakturkan (19.0: kosong). Diputuskan dev 2026-09-24.
- [ ] MF-03 — baris laporan dipisah per deskripsi baris SO (perubahan core Odoo 20). Total tidak berubah.
- [ ] Aset store (banner.gif, icon.png, index.html) diambil dari branch rilis `19.0`.
- [ ] 15 quirk lama (BSL-011…BSL-021: deteksi "Down payment" by nama, kolom tanpa konversi kurs, label field duplikat, dst.) sengaja TIDAK diperbaiki.

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
| User | | | |

## Penutupan Migrasi

- [ ] `doc/MIGRATION_CLOSED.md` ditulis dengan SHA HEAD `migration/20.0` — **SETELAH** sign-off di atas terisi (belum ditulis).
