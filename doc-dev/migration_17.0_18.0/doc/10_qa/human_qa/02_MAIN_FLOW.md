# Main Flow Test — advanced_sales_analysis

**Level:** Main Flow — flow bisnis inti sehari-hari.
**Estimasi waktu:** ~10 menit.
**Sumber:** S-02 di `../10_BUSINESS_FLOW_MIGRATION.md`.

```
1. Buat Sale Order baru, satu baris produk apa saja, harga 100, tanpa pajak.
2. Konfirmasi order (tombol "Confirm").
3. Buat invoice dari order itu (tombol "Create Invoice" → "Regular Invoice").
4. Post invoice (tombol "Confirm"/"Post").
5. Register payment penuh (tombol "Register Payment" → isi jumlah 100 → "Create Payment").
6. Buka Sales → Reporting → Sales.
7. Klik dropdown "Measures".
8. Aktifkan "Amount Received", "Waiting for Payment", "Amount To Invoice" (kalau belum aktif).
9. Filter/cari baris untuk order dari langkah 1.
```

**Hasil yang diharapkan:**
- Ketiga measure baru ("Amount Received", "Waiting for Payment", "Amount To Invoice") muncul di dropdown Measures, bisa dipilih.
- Untuk order yang sudah lunas penuh: "Amount Received" = 100, "Waiting for Payment" = 0, "Amount To Invoice" = 0.

## Hasil eksekusi

| Tanggal | Environment | Dijalankan oleh | Hasil | Catatan |
|---|---|---|---|---|
| | | | | |
