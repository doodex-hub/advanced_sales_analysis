# Main Flow Test — advanced_sales_analysis

**Level:** Main Flow — flow bisnis inti sehari-hari.
**Estimasi waktu:** ~12 menit.
**Sumber:** S-02 di `../10_BUSINESS_FLOW_MIGRATION.md`.

```
1. Buat Sale Order A: satu baris produk apa saja, harga 100, TANPA pajak.
2. Konfirmasi order A, buat invoice ("Create Invoice" -> "Regular Invoice"), post, register payment penuh (100).
3. Buat Sale Order B: satu baris produk dengan PAJAK price-included terpasang (mis. 10% termasuk pajak, harga 110).
4. Konfirmasi order B (ini menyentuh langsung jalur kode yang diperbaiki di migrasi 19.0 - fix DIFF-01).
5. Buka Sales -> Reporting -> Sales.
6. Klik dropdown "Measures".
7. Aktifkan "Amount Received", "Waiting for Payment", "Amount To Invoice" (kalau belum aktif).
8. Filter/cari baris untuk order A dan order B.
```

**Hasil yang diharapkan:**
- Ketiga measure baru muncul di dropdown Measures, bisa dipilih.
- Order A (lunas penuh, tanpa pajak): "Amount Received" = 100, "Waiting for Payment" = 0, "Amount To Invoice" = 0.
- Order B (ber-pajak, belum difakturkan): "Amount To Invoice" tampil dengan angka masuk akal (BUKAN kosong, BUKAN error) - ini yang membuktikan rename `tax_id`->`tax_ids` (DIFF-01) tidak merusak flow normal.

## Hasil eksekusi

| Tanggal | Environment | Dijalankan oleh | Hasil | Catatan |
|---|---|---|---|---|
| | | | | |
