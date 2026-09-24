# Main Flow — advanced_sales_analysis

**Level:** Main Flow. **Estimasi:** ~10 menit. **Sumber:** S-02.

```
1. Buat produk layanan "QA Service" harga 1000, tanpa pajak, invoicing policy "Ordered quantities".
2. Buat SO A: 1 x QA Service @1000 → Confirm → Create Invoice → Confirm → Register Payment penuh.
3. Buat SO B: 1 x QA Service @500 → Confirm → Create Invoice → Confirm → Register Payment 200.
4. Buat SO C: 1 x QA Service @1000 + 1 x @500 → Confirm (jangan difakturkan).
5. Sales → Reporting → Sales → Pivot, baris = Order Reference, measures = Amount Received, Waiting for Payment, Amount To Invoice.
```

**Hasil yang diharapkan:**

| Order | Amount Received | Waiting for Payment | Amount To Invoice |
|---|---|---|---|
| SO A | 1000 | 0 | 0 |
| SO B | 200 | 300 | 0 |
| SO C | 0 | 0 | 1500 |
| Total | 1200 | 300 | 1500 |

## Hasil eksekusi

| Tanggal | Environment | Dijalankan oleh | Hasil | Catatan |
|---|---|---|---|---|
| | | | | |
