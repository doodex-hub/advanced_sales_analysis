# Findings — advanced_sales_analysis (migrasi 18.0 → 19.0)

**Modul:** advanced_sales_analysis
**Migrasi:** 18.0 → 19.0
**Terakhir update:** 2026-08-26

---

## Ringkasan

| ID | Judul | Ditemukan di Step | Tag | Prioritas | Status |
|---|---|---|---|---|---|
| MF-01 | Core `sale.order.line.tax_id` di-rename `tax_ids` di 19.0 — modul memanggil field ini langsung, `AttributeError` kalau tidak difix | Step 2 (Diff Analysis) | `[GAP-MIGRASI]` | **Kritis** | ✅ **RESOLVED** 2026-08-26 — fix mekanis diterapkan langsung tanpa eskalasi (lihat catatan di bawah) |

---

## Detail

### MF-01 — Rename `sale.order.line.tax_id` → `tax_ids` di core 19.0
**Ditemukan di:** Step 2, 2026-08-26
**Tag:** `[GAP-MIGRASI]` — genuinely muncul karena perubahan core Odoo 19.0 (rename field), bukan bug yang diwarisi dari source 18.0.
**Ref:** `02_diff/02_DIFF_ANALYSIS.md` DIFF-01; `01_intake/01b_BASELINE_SPEC.md` `[BSL-008]` (method yang terdampak); `05_acceptance/05a_MIGRATION_ACCEPTANCE_CRITERIA.md` AC-06-03b (AC baru yang dibuat khusus untuk memverifikasi fix ini)
**Lokasi:** `advanced_sales_analysis/models/sale_report.py:114,118` (kode modul) vs `native-source` (`odoo18/addons/sale/models/sale_order_line.py:159-165`) / `native-target` (`enterprise19.0/odoo/addons/sale/models/sale_order_line.py:162-169`) (core)
**Deskripsi:** Core Odoo 19.0 me-rename field `sale.order.line.tax_id` (Many2many, `store=True`) jadi `tax_ids` (compute method juga ikut di-rename `_compute_tax_id`→`_compute_tax_ids`, ditambah `domain=` baru dan context key `hide_original_tax_ids`). Modul `advanced_sales_analysis` memanggil `line.tax_id.filtered(...)` dan `line.tax_id.compute_all(...)` langsung di `_compute_asa_amount_to_invoice()` — dua baris kode yang genuinely membaca field ini, bukan sekadar API yang "mungkin" terpengaruh.
**Dampak:** `AttributeError: 'sale.order.line' object has no attribute 'tax_id'` setiap kali method compute ini dieksekusi untuk baris SO ber-state `sale`/`done` — karena field ini `store=True`, dampaknya bukan cuma saat membuka report (compute dipicu saat write/recompute juga), jadi berpotensi memblokir konfirmasi order sama sekali kalau tidak diperbaiki.

**Kenapa tidak dieskalasi ke user (beda dari MF-01/MF-02 di migrasi 17→18 sebelumnya):** ini BUKAN kasus "ada beberapa cara valid dengan efek samping berbeda" — cuma ada SATU cara benar (ikut rename core, ganti `tax_id`→`tax_ids` di kode modul), tanpa trade-off apa pun (rename ini murni accessor, TIDAK mengubah semantik pajak sama sekali). Konsisten dengan `CLAUDE.md` §"Eksekusi Berkelanjutan di CLI": "kalau AI sudah punya rekomendasi yang jelas dan berisiko rendah, AI pilih rekomendasi itu sendiri, dokumentasikan alasannya, lalu LANJUT" — bukan kasus yang butuh keputusan pemilik modul seperti MF-01 (pilihan menerima behavior baru vs mempertahankan lama) atau MF-02 (trade-off rename field vs risiko fitur core rusak) di migrasi sebelumnya.

**Tindak lanjut (2026-08-26):**
- `advanced_sales_analysis/models/sale_report.py:114,118`: rename `line.tax_id`→`line.tax_ids` (lihat `06_implementation/06c_IMPLEMENTATION_LOG.md` [Fase A5]).
- `advanced_sales_analysis/tests/test_sale_order_line.py`: test baru `test_ac_06_03b_tax_ids_rename_price_include` ditambahkan khusus memverifikasi fix ini lewat jalur pajak `price_include` (jalur yang tidak tersentuh test lain).
- **Diverifikasi eksekusi (G1, 2026-08-26):** `0 failed, 0 error(s) of 39 tests`. Tidak ada warning/error baru selain yang sudah diketahui (`[BSL-017]`).

---

## Catatan

Tidak ada finding lain yang butuh keputusan pemilik modul di migrasi 18→19 ini — modul ini kecil dan sederhana (murni backend/compute, semua fase kondisional N/A), dan satu-satunya gap migrasi (MF-01 di atas) punya solusi tunggal yang jelas tanpa trade-off. Ini BERBEDA dari migrasi 17→18 sebelumnya yang punya 2 finding (MF-01, MF-02) yang genuinely butuh keputusan pemilik modul karena ada opsi valid lebih dari satu.

Gap yang TETAP terbuka (bukan finding baru, warisan dari migrasi sebelumnya, tidak butuh keputusan baru): AC-07-05 (UNION dengan `point_of_sale` terinstall — belum pernah diverifikasi eksekusi di versi manapun, 17.0/18.0/19.0). Lihat `05_acceptance/05a_MIGRATION_ACCEPTANCE_CRITERIA.md` dan `09_devtest/09_DEV_TESTING.md`.
