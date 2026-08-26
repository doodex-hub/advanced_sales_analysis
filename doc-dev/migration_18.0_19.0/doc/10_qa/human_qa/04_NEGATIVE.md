# Negative Test — advanced_sales_analysis

**Level:** Negative — guard/keamanan, hal yang HARUS ditolak/tidak boleh muncul. **WAJIB dijalankan minimal sekali sebelum rilis besar/UAT.**
**Estimasi waktu:** ~10 menit.
**Sumber:** S-04 di `../10_BUSINESS_FLOW_MIGRATION.md`. **Ini checklist PALING PENTING di folder ini** — satu-satunya verifikasi visual untuk fix DIFF-01 (`sale.order.line.tax_id` di-rename `tax_ids` di core Odoo 19.0, modul sudah disesuaikan).

**Konteks singkat (boleh dilewati kalau sudah paham):** Core Odoo 19.0 me-rename field `sale.order.line.tax_id` jadi `tax_ids`. Modul ini memanggil field itu langsung di `_compute_asa_amount_to_invoice` (2 tempat) — kalau tidak diperbaiki, method itu `AttributeError` setiap kali SO line dikonfirmasi/dihitung ulang (bukan cuma saat buka report). Fix sudah diverifikasi lewat test otomatis (39/39 pass, termasuk test baru khusus untuk fix ini), checklist ini verifikasi tambahan dari sisi tampilan/log server.

```
1. Buat Sale Order dengan SATU baris produk yang punya PAJAK terpasang (boleh price-included atau price-excluded, dua-duanya).
2. Konfirmasi order tersebut.
3. Cek log server (docker-env/logs/odoo.log atau log instance) — pastikan TIDAK ada traceback menyebut
   "AttributeError" dan "tax_id" bersamaan.
4. Buka pivot Sales Analysis, cari baris order dari langkah 1.
5. Cek measure "Amount To Invoice" tampil dengan angka (bukan kosong/error Python di layar).
6. Buat SATU Sale Order lagi dengan baris yang discount-nya di invoice DIBUAT BEDA dari discount di SO
   (invoice partial dengan diskon manual berbeda) — ini memaksa jalur kode yang paling dalam menyentuh
   pajak (`tax_ids.compute_all()`). Cek lagi log server bersih dari error yang sama.
```

**Hasil yang HARUS terjadi (guard):**
- TIDAK ADA error Python/traceback menyebut `tax_id`/`AttributeError` di mana pun selama langkah di atas.
- Measure "Amount To Invoice" tetap muncul dengan angka masuk akal untuk order ber-pajak.
- Nama measure di UI tetap sama seperti sebelumnya (rename `tax_id`->`tax_ids` murni internal, tidak terlihat user).

**Hasil yang TIDAK BOLEH terjadi:**
- Traceback `AttributeError: 'sale.order.line' object has no attribute 'tax_id'` di log manapun.
- Measure "Amount To Invoice" kosong/error untuk order ber-pajak (kalau ini terjadi, berarti fix DIFF-01 tidak lengkap atau ke-regress — eskalasi ke dev).

## Hasil eksekusi

| Tanggal | Environment | Dijalankan oleh | Hasil | Catatan |
|---|---|---|---|---|
| | | | | |
