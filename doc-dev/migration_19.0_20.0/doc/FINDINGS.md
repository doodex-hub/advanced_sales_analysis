# Findings — advanced_sales_analysis (migrasi 19.0 → 20.0)

**Modul:** advanced_sales_analysis
**Migrasi:** 19.0 → 20.0
**Terakhir update:** 2026-10-02

> Finding yang sengaja TETAP TERBUKA dari migrasi sebelumnya (tidak dicatat ulang sebagai finding baru): AC-07-05 (UNION `sale.report` dengan `point_of_sale` terinstall belum pernah dieksekusi di versi manapun), serta 15 quirk BSL-011…BSL-021 (`[DIWARISI-SOURCE]`, dipertahankan identik). Lihat `doc-dev/migration_18.0_19.0/doc/FINDINGS.md`.

---

## Ringkasan

| ID | Judul | Ditemukan di Step | Tag | Prioritas | Status |
|---|---|---|---|---|---|
| MF-01 | Hook `sale.report._select_additional_fields()` dihapus di 20.0 — 3 measure diam-diam 0/NULL, pivot crash `sum(text)` | Step 1 (pre-scan), dibuktikan Step 2 probe | `[GAP-MIGRASI]` | **Kritis** | ✅ RESOLVED 2026-09-24 — port `_select_dict` (commit `83e8719`), G1 A/B/C 0 failed of 43 |
| MF-02 | `pos_sale` 20.0 mengisi kolom modul `sale.report.amount_to_invoice` untuk baris POS (19.0: NULL) | Step 1 | `[GAP-MIGRASI]` | Rendah | ✅ DIPUTUSKAN dev 2026-09-24: terima & dokumentasikan |
| MF-03 | Core 20.0 menambah `l.name`/`l.product_uom_id` ke GROUP BY `sale.report` — granularitas baris laporan lebih halus | Step 2 | `[GAP-MIGRASI]` | Rendah | ✅ Diterima (preseden MF-01 17→18); dikonfirmasi pemilik project saat UAT sign-off 2026-09-24 |
| MF-04 | `account.move.amount_paid`/`amount_paid_cn` tidak di-reset ke 0 saat pembayaran di-unreconcile (field stored basi) | Review pasca-rilis 2026-10-02 | `[WARISAN-SOURCE]` | Rendah | ✅ DITERIMA 2026-10-02 — terbukti, tanpa dampak laporan, tidak diperbaiki |

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
**Keputusan pemilik modul:** tidak diperlukan (fix mekanis wajib).
**Tindak lanjut (2026-09-24):** `models/sale_report.py` `_select_dict()` (Fase A5). Bukti: test AC-07-01/01b/01c/04 + browser pivot FAIL di probe → PASS di Run A/B/C; test regresi baru `test_ac_07_06_select_dict_hook_dipakai`.

### MF-02 — Baris POS mendapat nilai `amount_to_invoice` di 20.0
**Ditemukan di:** Step 1 (2026-09-24)
**Tag:** `[GAP-MIGRASI]`
**Ref:** DIFF-02; AC-07-05 (warisan)
**Lokasi:** `odoo20/addons/pos_sale/report/sale_report.py:57`
**Deskripsi:** `_select_pos_dict()` native punya key `amount_to_invoice` (sisa dari versi lama; `sale.report` native 20.0 tidak punya field itu). Karena modul mendefinisikan `sale.report.amount_to_invoice`, cabang POS UNION mengisinya dengan subtotal POS yang belum difakturkan (× rate). Di 19.0 cabang POS selalu `NULL` untuk kolom modul.
**Dampak:** hanya bila `pos_sale` terinstall (bukan dependency modul). Total *Amount To Invoice* di pivot bertambah nilai POS belum difakturkan. `amount_received`/`waiting_for_payment` tetap NULL di baris POS.
**Keputusan pemilik modul:** Kuncoro, 2026-09-24 (dialog intake): **"Terima & dokumentasikan"** — tanpa override tambahan. (Gap eksekusi AC-07-05 tertutup di Step 9 Run C, lihat catatan di bawah.)

### MF-03 — Granularitas GROUP BY `sale.report` core 20.0
**Ditemukan di:** Step 2 (2026-09-24)
**Tag:** `[GAP-MIGRASI]` (perubahan core, bukan modul)
**Ref:** DIFF-06; `[BSL-023]` poin 2; preseden `doc-dev/migration_17.0_18.0/doc/FINDINGS.md` MF-01 (Opsi 1 disetujui)
**Deskripsi:** `_groupby_list()` 20.0 menambah `l.name` dan `l.product_uom_id`. Dua baris SO produk+harga sama tapi deskripsi beda kini jadi 2 baris laporan.
**Dampak:** hanya granularitas baris di view list/pivot tanpa group-by; total measure identik. Modul tidak meng-override GROUP BY sejak 17.0 dan tidak boleh mulai melakukannya.
**Keputusan:** diterima mengikuti preseden (AI, 2026-09-24, dicatat supaya dev bisa mengoreksi). Test regresi baru di Step 6 merekam perilaku 20.0.

---

### MF-04 — `amount_paid` / `amount_paid_cn` basi setelah unreconcile
**Ditemukan di:** review kode pasca-rilis (bukan migrasi), 2026-10-02. Diuji di Docker pada 18.0, 19.0, dan 20.0.
**Tag:** `[WARISAN-SOURCE]` — quirk lama (BSL-011), ada identik di 18.0/19.0/20.0.
**Lokasi:** `advanced_sales_analysis/models/sale_report.py` `AccountMove._compute_amount_paid`
**Deskripsi:** compute hanya meng-assign `amount_paid`/`amount_paid_cn` di dalam `if payment_state in [paid, in_payment, partial]`. Tanpa assign, compute stored di core tidak menimpa nilai lama (`odoo/orm/fields.py` `compute_value`), jadi nilai tetap bila faktur kembali ke `not_paid`.
**Reproduksi:** SO 100 → faktur diposting → bayar penuh (`amount_paid`=100) → `account.move.line.remove_move_reconcile` pada baris receivable. Hasil di 18/19/20 sama: `payment_state`=not_paid, `amount_residual`=100, **`amount_paid` tetap 100**.
**Dampak:** tidak ada pada laporan. `sale.order.line.amount_received`=0 dan `waiting_for_payment`=100 langsung benar setelah unreconcile, karena nilai `amount_paid` hanya dibaca saat faktur berstatus bayar, dan saat itu compute dijalankan ulang (depends `amount_residual`). Hanya field stored di faktur yang basi; tidak ada view atau consumer lain.
**Keputusan:** diterima, tidak diperbaiki (kode dipertahankan). Kalau diperbaiki kelak: `move.amount_paid = move.amount_paid_cn = 0.0` di awal loop, bump patch, publish 18/19/20 sekaligus.
**Dugaan yang dibantah pada review yang sama:** deteksi uang muka via nama produk `"Down payment"` (BSL-013). Skenario DP 50% → bayar DP → faktur akhir → bayar penuh menghasilkan angka identik di 18/19/20 dan total akhir benar (Amount Received 100, Waiting 0). Di 19/20 baris DP tidak punya produk sehingga cabang nama itu tidak pernah aktif, tanpa efek ke angka akhir.
**Catatan penomoran:** ID MF-04 diseragamkan dengan FINDINGS 19.0→20.0 atas permintaan pemilik project.

---

## Catatan — gap warisan AC-07-05 TERTUTUP (2026-09-24)

Run C Step 9 (`-i advanced_sales_analysis,pos_sale`, Odoo 20.0): `test_f19_union_kompatibel_dengan_point_of_sale` dijalankan (tidak skip) dan PASS — UNION `sale.report` dengan POS terinstall dieksekusi nyata untuk pertama kalinya sejak 17.0. Perilaku nilai baris POS untuk `amount_to_invoice` tetap sesuai MF-02 (diterima).
