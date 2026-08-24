# Findings — advanced_sales_analysis (migrasi 17.0 → 18.0)

**Modul:** advanced_sales_analysis
**Migrasi:** 17.0 → 18.0
**Terakhir update:** 2026-08-21

---

## Ringkasan

| ID | Judul | Ditemukan di Step | Tag | Prioritas | Status |
|---|---|---|---|---|---|
| MF-01 | Core `sale.report._group_by_sale()` 18.0 menambah kolom GROUP BY (`price_unit`, `invoice_status`, `is_downpayment`) & menghapus `analytic_account_id` — granularitas laporan berubah independen dari modul ini | Step 6 (G1, eksekusi nyata) | `[GAP-MIGRASI]` | **Tinggi** | ✅ **RESOLVED** 2026-08-21 — Opsi 1 disetujui pemilik modul |
| MF-02 | Core `sale` 18.0 menambah field BARU `sale.order.line.amount_to_invoice` (Monetary) — nama PERSIS SAMA dengan field modul ini, ditimpa total, merusak rantai credit-limit partner core | Step 8 (Code Review, cek tabrakan nama method) | `[GAP-MIGRASI]` | **KRITIS** | ✅ **RESOLVED** 2026-08-21 — Opsi 2 (rename field), diverifikasi G1 (0 failed, 0 error of 38 tests) |

---

## Detail

### MF-01 — Granularitas `sale.report` berubah di 18.0 karena core, bukan karena modul ini
**Ditemukan di:** Step 6, G1 install test run #2 (2026-08-21) — `test_ac_07_03_group_by_tidak_lagi_memecah_baris` FAIL: `AssertionError: 2 != 1`.
**Tag:** `[GAP-MIGRASI]`
**Ref:** `02_diff/02_DIFF_ANALYSIS.md` DIFF-01 (analisis Step 2 di baris ini TERBUKTI TIDAK LENGKAP — cuma mengecek alias tabel currency berubah nama, TIDAK mengecek daftar kolom `_group_by_sale()` secara menyeluruh); `01_intake/01b_BASELINE_SPEC.md` `[BSL-023]`; `doc-dev/backfill/FINDINGS.md` F-06/F-19 (source, sudah RESOLVED di 17.0 — finding ini BUKAN F-06 kambuh, ini gap baru independen)
**Lokasi:** `native-target` (18.0) `addons/sale/report/sale_report.py` — method `_group_by_sale()`, dibandingkan ke `native-source` (17.0) method yang sama

**Deskripsi:** Perbandingan langsung `_group_by_sale()` core 17.0 vs 18.0 (bukan cuma dicek "nama method sama" seperti Step 2, tapi ISI kolomnya satu-per-satu):

| Kolom | 17.0 | 18.0 |
|---|---|---|
| `l.price_unit` | Tidak ada | **Ditambahkan** |
| `l.invoice_status` | Tidak ada | **Ditambahkan** |
| `l.is_downpayment` | Tidak ada | **Ditambahkan** |
| `s.analytic_account_id` | Ada | **Dihapus** |
| (sisanya) | — | Identik |

`advanced_sales_analysis` **tidak** override `_group_by_sale()` (sudah dihapus lewat fix F-19 di source 17.0, diganti `_select_additional_fields()`) — modul ini sepenuhnya memakai GROUP BY bawaan core, apa pun isinya. Konsekuensinya: perubahan granularitas ini murni akibat Odoo 18.0 sendiri, TIDAK ADA hubungannya dengan kode modul ini maupun dengan fix F-19/F-06/F-08.

**Dampak:** Test `test_ac_07_03_group_by_tidak_lagi_memecah_baris` (dua baris SO produk sama, `price_unit` beda: 60.0 dan 40.0) — di 17.0 kedua baris MENYATU jadi 1 row laporan (`price_unit` bukan bagian GROUP BY 17.0). Di 18.0, `price_unit` SEKARANG bagian GROUP BY core → kedua baris **terpecah jadi 2 row**. Efeknya BUKAN cuma test ini: **setiap SO dengan ≥2 baris produk sama tapi `price_unit`/`invoice_status`/`is_downpayment` berbeda akan menghasilkan LEBIH BANYAK baris di Sales Analysis 18.0 dibanding 17.0** — berlaku untuk laporan core Odoo apa pun (bukan spesifik modul ini), tapi baru "ketahuan" lewat test modul ini karena modul ini yang paling dulu diverifikasi lewat eksekusi nyata terhadap 18.0.

**Kenapa ini genuinely butuh keputusan, bukan sekadar "kode menang, lanjut":**
1. **Opsi A — Terima behavior baru apa adanya (Rekomendasi AI):** Tidak ubah kode modul sama sekali. Update `test_ac_07_03_group_by_tidak_lagi_memecah_baris` supaya assertion-nya sesuai baseline 18.0 yang BENAR (`len(rows) == 2` untuk skenario ini, bukan `1`), dengan catatan eksplisit di test bahwa ini BUKAN regresi modul, murni core Odoo 18.0. **Risiko:** Rendah secara teknis (tidak ada kode custom yang disentuh, konsisten filosofi "port kode saja"), TAPI end-user (finance/sales manager) yang familiar dengan tampilan 17.0 akan melihat Sales Analysis 18.0 punya LEBIH BANYAK baris untuk data yang sama — perubahan tampilan yang terlihat, meski bukan bug.
2. **Opsi B — Coba pertahankan granularitas 17.0 dengan override `_group_by_sale()` manual** (strip 3 kolom baru core dari GROUP BY). **Risiko: Tinggi** — ini PERSIS pola yang baru saja dihapus lewat fix F-19 (override manual `_group_by_sale()` dengan string SQL) karena rawan UNION column mismatch dan rapuh terhadap perubahan core. Mengembalikan pola ini berisiko menghidupkan kembali kelas bug yang sama, DAN ini technically bukan "port kode 1:1" lagi — itu perubahan behavior yang disengaja (mengubah bagaimana core bekerja), yang menurut `01a_MIGRATION_INTAKE.md` §5 butuh disetujui eksplisit sebagai penyimpangan, bukan diam-diam dilakukan.
3. **Opsi C — Eskalasi ke business user dulu** sebelum memutuskan A/B — kalau granularitas laporan ini sensitif secara bisnis (mis. dipakai untuk rekonsiliasi finansial yang mengasumsikan row-count tertentu), keputusan sebaiknya bukan murni teknis.

**Rekomendasi AI:** Opsi A. Alasan: (1) ini genuinely bukan sesuatu yang modul ini "rusak" — core Odoo sendiri yang berubah, memaksakan granularitas lama berarti melawan arah desain core 18.0; (2) Opsi B membawa risiko teknis nyata yang baru saja dihindari lewat fix F-19; (3) pertambahan baris laporan (bukan pengurangan/kehilangan data) — informasi tetap ada, cuma disajikan lebih granular, sesuai arah Odoo sendiri.

**Keputusan pemilik modul:** ✅ **Opsi 1 disetujui** (2026-08-21) — "ini gap yang terjadi di migrasi, baik pilih opsi 1". Behavior baru 18.0 (granularitas lebih detail, ditentukan core) diterima apa adanya, TIDAK di-override balik ke perilaku 17.0.

**Tindak lanjut yang dilakukan (2026-08-21):**
- `advanced_sales_analysis/tests/test_sale_report.py`: `test_ac_07_03_group_by_tidak_lagi_memecah_baris` di-rename jadi `test_ac_07_03_group_by_granularitas_18_0`, assertion diubah dari `len(rows) == 1` (baseline 17.0) jadi `len(rows) == 2` (baseline 18.0 yang benar), docstring dan pesan assertion dirujuk balik ke MF-01 ini.
- `01_intake/01a_MIGRATION_INTAKE.md` §5 (Scope Boundary): ditambah entry "yang sengaja diubah" untuk granularitas `sale.report` GROUP BY.
- `01_intake/01b_BASELINE_SPEC.md` `[BSL-023]`: ditambah catatan bahwa klaim "granularitas sama seperti core" TIDAK bisa dipertahankan identik 17.0↔18.0 — ini penyimpangan disetujui, bukan gap yang masih terbuka.
- `05_acceptance/05a_MIGRATION_ACCEPTANCE_CRITERIA.md` AC-07-03: diperbarui merefleksikan baseline 18.0 (2 baris), bukan 17.0 (1 baris).
- G1 di-re-run setelah fix test — lihat `06_implementation/06c_IMPLEMENTATION_LOG.md`.

---

### MF-02 — Kolisi field BARU `sale.order.line.amount_to_invoice` dengan core 18.0 — merusak credit limit partner
**Ditemukan di:** Step 8 (Code Review, checklist WAJIB "cek tabrakan nama method dengan core"), 2026-08-21
**Tag:** `[GAP-MIGRASI]` — **BUKAN** `[DIWARISI-SOURCE]`: kolisi ini genuinely baru muncul karena field core yang di-collide TIDAK ADA di 17.0 sama sekali, jadi tidak mungkin "sudah ada sejak 17.0 dan dipertahankan".
**Ref:** `08_review/08_CODE_REVIEW.md` CR-01; `01_intake/01b_BASELINE_SPEC.md` `[BSL-008]` (field modul `sale.order.line.amount_to_invoice`)
**Lokasi:** `advanced_sales_analysis/models/sale_report.py:88-90` (field+method modul) vs `native-target` `addons/sale/models/sale_order_line.py:294-298,1134-1142` (field+method core BARU), `addons/sale/models/sale_order.py:239,754-757` (field turunan `sale.order.amount_to_invoice`), `addons/sale/models/account_move.py:165-200` (konsumen: credit limit), `addons/sale/models/res_partner.py:100` (konsumen: stat button)

**Deskripsi:** Core Odoo 18.0 menambahkan field BARU `sale.order.line.amount_to_invoice` (`Monetary`, `compute='_compute_amount_to_invoice'`, `compute_sudo=True`) — field ini **tidak ada di 17.0** (17.0 cuma punya `untaxed_amount_to_invoice`, nama berbeda). Modul `advanced_sales_analysis` sudah lebih dulu mendefinisikan field dengan **nama field DAN nama method compute yang PERSIS SAMA** (`amount_to_invoice`/`_compute_amount_to_invoice`) di model yang SAMA, dengan semantik yang jauh berbeda (Float, `price_subtotal − (waiting_for_payment + amount_received)`, vs Monetary core `unit_price_total × qty_to_invoice` berbasis `qty_invoiced_posted`).

Karena `advanced_sales_analysis` `depends` langsung ke `sale` (load registry SETELAH `sale`), definisi modul **menimpa total** definisi dan compute core — dikonfirmasi dari log instalasi G1 (cuma satu baris "Prepare computation of sale.order.line.amount_to_invoice", tidak ada warning tipe field berbeda antar modul, tidak ada jejak method core pernah terpanggil).

**Rantai dampak (dikonfirmasi baca kode `native-target` langsung, BELUM diverifikasi eksekusi end-to-end dengan credit limit aktif):**
1. `sale.order.line.amount_to_invoice` → semantik modul menang (bukan semantik core "Un-invoiced Balance" tax-inclusive).
2. `sale.order.amount_to_invoice` (`@api.depends('order_line.amount_to_invoice')`, field core LAIN yang TIDAK disentuh modul ini) ikut menghitung dari nilai yang salah semantiknya.
3. `account.move._get_partner_credit_warning_exclude_amount()` dan `_compute_partner_credit()` (core `sale`, extend `account_move`) memakai `order.amount_to_invoice` untuk **kalkulasi credit limit/warning kredit partner** saat invoice dikonfirmasi.
4. `res.partner` stat button "amount to invoice" (`res_partner.py:100`) ikut memakai agregat yang salah semantiknya.

**Dampak:** Kalau database target 18.0 mengaktifkan fitur **Credit Limit** (Settings → Invoicing → Credit Limit, `res.partner.credit_limit` + `use_partner_credit_limit`), warning/blokir invoice berbasis credit limit akan memakai angka yang salah — bisa false-negative (invoice yang seharusnya diwarning tidak diwarning) atau false-positive, tergantung data. Kalau fitur Credit Limit TIDAK dipakai sama sekali di database target, dampak riil = 0 (cuma field UI/stat button yang menampilkan angka tidak akurat, tidak ada blocking logic yang jalan).

**Kenapa ini genuinely butuh keputusan, bukan sekadar "kode menang, lanjut":** Ini BUKAN kasus "dipertahankan sesuai prinsip source-of-truth" (F-01 di 17.0) — field core yang di-collide baru lahir di 18.0. Migrasi "port 1:1" tidak otomatis berarti "biarkan field baru core rusak" — tapi mengganti nama field JUGA menyalahi prinsip "jangan rename field kecuali wajib untuk kompatibilitas" (dan field ini yang mungkin dipakai di export/filter/dashboard existing kalau modul sudah dipakai di 17.0 production).

**Opsi:**
1. **Terima kolisi apa adanya (port 1:1 murni, tidak override nama field).** Risiko: **Tinggi** KALAU Credit Limit dipakai (perhitungan kredit partner jadi salah, silent — tidak ada error/warning); **Nihil** kalau Credit Limit tidak dipakai. Konsisten "port kode saja" tanpa deviasi.
2. **Rename field modul** (`amount_to_invoice` → mis. `x_asa_amount_to_invoice` atau `amount_to_invoice_cn`-style namespace sendiri, ikut sesuaikan referensi internal: `_compute_amount_to_invoice`→`_compute_asa_amount_to_invoice`, dan turunannya di `sale.report`/`_select_additional_fields()`). Risiko: **Sedang** — field core `sale.order.line`/`sale.order`/credit-limit kembali berfungsi normal, TAPI ini genuinely rename field yang bisa memutus export/filter/API pihak ketiga yang sudah memakai nama `amount_to_invoice` (kalau modul sudah dipakai production 17.0). Ini persis rekomendasi lama F-01 (yang sampai sekarang belum dieksekusi untuk `account.move.amount_paid`) — kalau Opsi 2 dipilih di sini, pertimbangkan juga apakah F-01 sebaiknya ikut diselesaikan sekalian (pertanyaan terbuka, BUKAN otomatis termasuk scope MF-02 kecuali user minta).
3. **Cek dulu ke business user apakah Credit Limit dipakai** sebelum putuskan 1/2 — kalau tidak dipakai sama sekali, Opsi 1 aman sepenuhnya tanpa risiko.

**Rekomendasi AI:** Opsi 3 dulu (tanya apakah Credit Limit dipakai), lalu: kalau TIDAK dipakai → Opsi 1 (paling sederhana, sesuai "port kode saja"); kalau DIPAKAI → Opsi 2 (rename), karena merusak fitur financial core secara silent adalah risiko yang tidak proporsional dibanding effort rename satu field.

**Keputusan pemilik modul:** ✅ **Opsi 2 disetujui** (2026-08-21) — "Pakai opsi 2 untuk issue code review". Field `sale.order.line.amount_to_invoice` di-rename ke `asa_amount_to_invoice` (namespace modul), method compute ikut di-rename `_compute_amount_to_invoice`→`_compute_asa_amount_to_invoice`.

**Tindak lanjut (2026-08-21):**
- `advanced_sales_analysis/tests/test_sale_order_line.py`, `test_account_move.py`: semua rujukan `amount_to_invoice` pada `sale.order.line` diperbarui ke `asa_amount_to_invoice` (`sale.report.amount_to_invoice` TIDAK berubah — field level laporan, tidak collide dengan core).
- `advanced_sales_analysis/models/sale_report.py`: awalnya **BLOCKED** oleh `.claude/settings.json` deny rule (`Edit(**/models/**)`) — AI tidak bisa menulis langsung ke `models/`, dan tidak diizinkan mengubah `settings.json` sendiri (diblokir classifier level lebih tinggi, bahkan setelah user meminta eksplisit di chat — perubahan permission WAJIB dilakukan user sendiri di luar sesi). User melonggarkan deny rule secara manual, AI lanjut menerapkan rename: field `amount_to_invoice`→`asa_amount_to_invoice`, method `_compute_amount_to_invoice`→`_compute_asa_amount_to_invoice`, 2 `@api.depends` string diupdate. `sale.report.amount_to_invoice` (dict key `_select_additional_fields()`) TIDAK diubah, cuma sumber SQL-nya (`l.amount_to_invoice`→`l.asa_amount_to_invoice`).
- **Diverifikasi eksekusi (G1, 2026-08-21 03:12):** `0 failed, 0 error(s) of 38 tests`. Tidak ada warning baru (tipe field/label) akibat rename — cuma warning F-13 lama yang sudah diketahui, sekarang menyebut `asa_amount_to_invoice` (bukan `amount_to_invoice`), konsisten.
