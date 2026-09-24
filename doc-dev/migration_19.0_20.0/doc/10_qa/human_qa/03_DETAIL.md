# Detail — advanced_sales_analysis

**Level:** Detail. **Estimasi:** ~20 menit. **Sumber:** S-03, S-04, S-05. Semua quirk di bawah SENGAJA dipertahankan identik 19.0 — jangan dilaporkan sebagai bug baru.

```
1. Uang muka: SO 1000 → Create Invoice "Down payment (percentage)" 30% → Confirm, belum dibayar.
   Buka pivot: baris "Down payment" Waiting for Payment = 300.
2. Mata uang lain: pricelist EUR (kurs 2), SO 100 EUR, fakturkan & bayar penuh.
   Pivot: Untaxed Total = 50 (dikonversi), Amount Received = 100 (TIDAK dikonversi — perilaku lama).
3. Deskripsi baris: SO dengan 2 baris produk & harga sama, deskripsi beda → 2 baris di laporan list
   (perubahan core Odoo 20, FINDINGS MF-03); total tetap sama.
4. (Opsional, kalau POS dipakai) dengan Point of Sale terinstall: Sales Analysis tetap terbuka normal.
   Baris POS dapat nilai di "Amount To Invoice" (FINDINGS MF-02, diterima).
```

## Hasil eksekusi

| Tanggal | Environment | Dijalankan oleh | Hasil | Catatan |
|---|---|---|---|---|
| | | | | |
