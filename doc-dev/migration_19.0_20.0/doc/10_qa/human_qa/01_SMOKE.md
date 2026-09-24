# Smoke Test — advanced_sales_analysis

**Level:** Smoke — kalau gagal: STOP, balik ke Step 9 / eskalasi dev.
**Estimasi:** ~3 menit. **Sumber:** S-01.

```
1. Login ke Odoo 20.0 tempat advanced_sales_analysis terinstall.
2. Buka Sales → Reporting → Sales.
3. Klik tombol view Pivot.
4. Klik "Measures", centang "Amount Received".
```

**Hasil yang diharapkan:** Dropdown Measures berisi "Amount Received", "Waiting for Payment", "Amount To Invoice"; kolom Amount Received muncul di pivot. TIDAK ADA error "function sum(text) does not exist" (tanda port `_select_dict` hilang/ke-regress).

## Hasil eksekusi

| Tanggal | Environment | Dijalankan oleh | Hasil | Catatan |
|---|---|---|---|---|
| | | | | |
