# Smoke Test — advanced_sales_analysis

**Level:** Smoke — kalau langkah ini gagal: STOP, jangan lanjut deploy/testing lain, balik ke Step 9 atau eskalasi ke tim dev.
**Estimasi waktu:** ~3 menit.
**Sumber:** S-01 di `../10_BUSINESS_FLOW_MIGRATION.md`. Bukti otomatis pendukung sudah Pass di Step 9 (`test_qa_measures_baru_tersedia_di_pivot_sales_analysis`) — checklist ini double-check independen.

```
1. Login sebagai admin ke instance Odoo 18.0 tempat advanced_sales_analysis diinstall.
2. Buka menu Sales → Reporting → Sales.
3. Tunggu pivot table terbuka.
```

**Hasil yang diharapkan:** Pivot terbuka normal, tidak ada halaman error/traceback (khususnya JANGAN ada error menyebut "UNION" atau "each UNION query must have the same number of columns" — itu regresi F-19 yang seharusnya sudah diperbaiki permanen).

## Hasil eksekusi

| Tanggal | Environment | Dijalankan oleh | Hasil | Catatan |
|---|---|---|---|---|
| | | | | |
