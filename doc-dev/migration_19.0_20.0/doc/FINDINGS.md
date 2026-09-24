# Findings — advanced_sales_analysis (migrasi 19.0 → 20.0)

**Modul:** advanced_sales_analysis
**Migrasi:** 19.0 → 20.0
**Terakhir update:** 2026-09-24

> Finding yang sengaja TETAP TERBUKA dari migrasi sebelumnya (tidak dicatat ulang sebagai finding baru): AC-07-05 (UNION `sale.report` dengan `point_of_sale` terinstall belum pernah dieksekusi di versi manapun), serta 15 quirk BSL-011…BSL-021 (`[DIWARISI-SOURCE]`, dipertahankan identik). Lihat `doc-dev/migration_18.0_19.0/doc/FINDINGS.md`.

---

## Ringkasan

| ID | Judul | Ditemukan di Step | Tag | Prioritas | Status |
|---|---|---|---|---|---|
| MF-01 | Hook `sale.report._select_additional_fields()` dihapus di 20.0 — 3 measure diam-diam 0/NULL, pivot crash `sum(text)` | Step 1 (pre-scan), dibuktikan Step 2 probe | `[GAP-MIGRASI]` | **Kritis** | 🔄 Fix di Step 6 (satu cara benar, tanpa eskalasi) |
| MF-02 | `pos_sale` 20.0 mengisi kolom modul `sale.report.amount_to_invoice` untuk baris POS (19.0: NULL) | Step 1 | `[GAP-MIGRASI]` | Rendah | ✅ DIPUTUSKAN dev 2026-09-24: terima & dokumentasikan |
| MF-03 | Core 20.0 menambah `l.name`/`l.product_uom_id` ke GROUP BY `sale.report` — granularitas baris laporan lebih halus | Step 2 | `[GAP-MIGRASI]` | Rendah | ✅ Diterima (preseden MF-01 17→18) — dev boleh mengoreksi |

---

## Detail

### MF-01 — `_select_additional_fields()` dihapus di core 20.0
**Ditemukan di:** Step 1 (scan core sebelum dialog intake), dibuktikan probe eksekusi Step 2 (2026-09-24)
**Tag:** `[GAP-MIGRASI]`
**Ref:** `02_DIFF_ANALYSIS.md` DIFF-01; `01b_BASELINE_SPEC.md` `[BSL-005]`, `[BSL-014]`, `[BSL-023]`
**Lokasi:** `advanced_sales_analysis/models/sale_report.py:13-18` vs `odoo20/addons/sale/report/sale_report.py:123-189`
**Deskripsi:** `sale.report` 20.0 membangun query lewat `_table_sql` → `_select_dict(table: TableSQL)` (dict `SQL`), bukan string `_select_sale()` + `_select_additional_fields()`. Override modul tetap ter-load tapi tidak pernah dipanggil; `_select_dict_to_list()` mengisi field stored yang tidak ada di dict dengan `NULL`.
**Dampak (terbukti probe):** `sale.report` ORM → 3 kolom bernilai 0.0 (4 test AC-07 FAIL); pivot Sales Analysis + measure modul → `function sum(text) does not exist` (HTTP 500, test browser FAIL). Install sukses, tanpa warning — silent sampai laporan dipakai.
**Rekomendasi:** override `_select_dict(table)` dengan ekspresi SQL setara 1:1 (guard `product_id IS NOT NULL`, `SUM` tanpa kurs). Tidak ada opsi alternatif dengan efek bisnis berbeda → tidak dieskalasi (prinsip "Eksekusi Berkelanjutan", sama dengan MF-01 18→19).
**Keputusan pemilik modul:** tidak diperlukan (fix mekanis wajib). Status akhir diisi Step 6.

### MF-02 — Baris POS mendapat nilai `amount_to_invoice` di 20.0
**Ditemukan di:** Step 1 (2026-09-24)
**Tag:** `[GAP-MIGRASI]`
**Ref:** DIFF-02; AC-07-05 (warisan)
**Lokasi:** `odoo20/addons/pos_sale/report/sale_report.py:57`
**Deskripsi:** `_select_pos_dict()` native punya key `amount_to_invoice` (sisa dari versi lama; `sale.report` native 20.0 tidak punya field itu). Karena modul mendefinisikan `sale.report.amount_to_invoice`, cabang POS UNION mengisinya dengan subtotal POS yang belum difakturkan (× rate). Di 19.0 cabang POS selalu `NULL` untuk kolom modul.
**Dampak:** hanya bila `pos_sale` terinstall (bukan dependency modul). Total *Amount To Invoice* di pivot bertambah nilai POS belum difakturkan. `amount_received`/`waiting_for_payment` tetap NULL di baris POS.
**Keputusan pemilik modul:** Kuncoro, 2026-09-24 (dialog intake): **"Terima & dokumentasikan"** — tanpa override tambahan. AC-07-05 tetap gap eksekusi terbuka.

### MF-03 — Granularitas GROUP BY `sale.report` core 20.0
**Ditemukan di:** Step 2 (2026-09-24)
**Tag:** `[GAP-MIGRASI]` (perubahan core, bukan modul)
**Ref:** DIFF-06; `[BSL-023]` poin 2; preseden `doc-dev/migration_17.0_18.0/doc/FINDINGS.md` MF-01 (Opsi 1 disetujui)
**Deskripsi:** `_groupby_list()` 20.0 menambah `l.name` dan `l.product_uom_id`. Dua baris SO produk+harga sama tapi deskripsi beda kini jadi 2 baris laporan.
**Dampak:** hanya granularitas baris di view list/pivot tanpa group-by; total measure identik. Modul tidak meng-override GROUP BY sejak 17.0 dan tidak boleh mulai melakukannya.
**Keputusan:** diterima mengikuti preseden (AI, 2026-09-24, dicatat supaya dev bisa mengoreksi). Test regresi baru di Step 6 merekam perilaku 20.0.
