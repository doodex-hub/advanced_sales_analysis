# Negative Test — advanced_sales_analysis

**Level:** Negative — guard/keamanan, hal yang HARUS ditolak/tidak boleh muncul. **WAJIB dijalankan minimal sekali sebelum rilis besar/UAT.**
**Estimasi waktu:** ~10 menit.
**Sumber:** S-04 di `../10_BUSINESS_FLOW_MIGRATION.md`. **Ini checklist PALING PENTING di folder ini** — satu-satunya verifikasi visual untuk perbaikan MF-02 (kolisi nama field dengan core Odoo 18.0, sudah diperbaiki lewat rename `amount_to_invoice` → `asa_amount_to_invoice` khusus di `sale.order.line`).

**Konteks singkat (boleh dilewati kalau sudah paham):** Sebelum diperbaiki, modul ini menimpa total field baru core `sale.order.line.amount_to_invoice` yang dipakai fitur Credit Limit partner — kalau tidak diperbaiki, angka credit limit warning bisa salah secara diam-diam (tanpa error). Fix-nya sudah diverifikasi lewat test otomatis (38/38 pass), checklist ini verifikasi tambahan dari sisi tampilan.

```
1. Buka Settings → Invoicing (atau Accounting) → cek apakah "Credit Limit" (Payment Terms/Credit Limit section) AKTIF di instance ini.
   - Kalau TIDAK aktif: catat "Credit Limit tidak dipakai di instance ini" di kolom Catatan, lalu LANGSUNG ke langkah 5 (skip 2-4).
2. Buka contact/partner (Customers) yang punya Credit Limit diisi (angka > 0).
3. Buat Sale Order + invoice untuk partner itu dengan nilai MELEBIHI credit limit-nya.
4. Post invoice — cek apakah warning credit limit muncul (atau tidak muncul, sesuai konfigurasi) SAMA seperti sebelum modul advanced_sales_analysis diinstall (kalau ada cara bandingkan) — atau minimal, warning-nya masuk akal (bukan angka aneh/kosong/error Python di layar).
5. Buka Sale Order apa pun yang punya sisa tagihan (belum full invoiced).
6. Cek stat button/field "Amount to Invoice" atau "Un-invoiced Balance" di form Sale Order (kalau ada di layout 18.0 default) — pastikan menampilkan angka (bukan kosong/error), TIDAK crash.
7. Buka Sales Analysis, cek 3 measure modul ini (Amount Received/Waiting for Payment/Amount To Invoice) — nama measure di UI harus SAMA seperti sebelumnya (rename cuma teknis, bukan di label yang dilihat user).
```

**Hasil yang HARUS terjadi (guard):**
- TIDAK ADA error Python/traceback di mana pun selama langkah di atas.
- Kalau Credit Limit dipakai: warning-nya berbasis angka yang masuk akal (bukan angka yang jelas salah — misal negatif ekstrem atau jauh dari yang diharapkan).
- 3 measure modul tetap muncul dengan LABEL yang sama seperti sebelum migrasi — user tidak melihat nama field teknis (`asa_amount_to_invoice`) di mana pun di UI.

**Hasil yang TIDAK BOLEH terjadi:**
- Field/stat button core (`amount_to_invoice`/"Un-invoiced Balance") kosong atau error karena bentrok nama.
- Measure modul hilang dari dropdown atau berubah nama jadi `asa_amount_to_invoice` di UI (kalau ini terjadi, berarti rename tidak lengkap — eskalasi ke dev).

## Hasil eksekusi

| Tanggal | Environment | Dijalankan oleh | Hasil | Catatan |
|---|---|---|---|---|
| | | | | |
