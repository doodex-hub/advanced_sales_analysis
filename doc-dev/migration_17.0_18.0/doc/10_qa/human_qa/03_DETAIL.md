# Detail Test — advanced_sales_analysis

**Level:** Detail — varian/edge-case, biasanya bisa ditunda ke rilis berikutnya kalau disepakati eksplisit.
**Estimasi waktu:** ~15 menit.
**Sumber:** S-03 di `../10_BUSINESS_FLOW_MIGRATION.md`.

> **Catatan penting sebelum mulai:** beberapa perilaku di bawah ini adalah BUG YANG DIKETAHUI dan SENGAJA DIPERTAHANKAN dari versi 17.0 (bukan sesuatu yang perlu dilaporkan ulang sebagai temuan baru) — lihat `FINDINGS.md`/`01b_BASELINE_SPEC.md` untuk detail F-04/F-05. Tujuan checklist ini adalah memastikan behavior-nya **tetap sama** seperti sebelumnya, bukan mengecek "apakah sudah benar".

```
1. Buat Sale Order dengan uang muka (down payment): gunakan tombol "Create Invoice" → pilih "Down payment" → invoice sebagian.
2. Post invoice uang muka, register payment sebagian saja (jangan lunas penuh).
3. Buat Sale Order dalam mata uang ASING (beda dari mata uang perusahaan) — konfirmasi, invoice, bayar sebagian.
4. Buka Sales Analysis, aktifkan ketiga measure baru.
5. Amati baris untuk order dari langkah 1-2 (uang muka) dan langkah 3 (multi-currency).
```

**Hasil yang diharapkan (bug yang DIPERTAHANKAN, bukan "seharusnya benar"):**
- Baris uang muka: nilai measure dihitung lewat jalur khusus DP, mungkin terlihat tidak proporsional dibanding baris biasa — ini NORMAL untuk versi ini.
- Baris multi-currency: kolom `Total` (core) sudah dikonversi ke mata uang perusahaan, TAPI "Amount Received"/"Waiting for Payment"/"Amount To Invoice" TIDAK dikonversi — angkanya jadi tidak "nyambung" secara matematis dengan kolom Total di baris yang sama. **Ini bug F-05 yang sudah diketahui sejak 17.0, JANGAN dilaporkan sebagai bug baru** — cukup konfirmasi masih berperilaku sama (belum berubah tanpa sengaja).

## Hasil eksekusi

| Tanggal | Environment | Dijalankan oleh | Hasil | Catatan |
|---|---|---|---|---|
| | | | | |
