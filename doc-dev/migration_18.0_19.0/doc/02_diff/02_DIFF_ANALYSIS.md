# Diff & Compatibility Analysis — advanced_sales_analysis

**Step:** 2 — Diff & Compatibility Analysis
**Versi:** 18.0 → 19.0
**Tanggal:** 2026-08-26
**Ref:** `01_intake/01a_MIGRATION_INTAKE.md`, `migration-tool/knowledge/`

---

## 0. Knowledge Base Check

| Sumber | Sudah ada entry? | Lokasi |
|---|---|---|
| `version-diffs/18-to-19.md` | Ya — tapi **riset di muka, belum ada project migrasi nyata sebelumnya**. Dicek: tidak ada satu pun item §1/§2 yang relevan ke modul ini (modul tidak menyentuh `res.groups`, controller route, `_sql_constraints`, domain expression, view search `<group>`, testing demo data, dst — konsisten dengan Applicability Check `01a` §2b, semua fase kondisional N/A). | `migration-tool/knowledge/version-diffs/18-to-19.md` |
| `dependency-compat/sale_report/17-to-18.md`, `dependency-compat/account_payment/17-to-18.md` | Ya, tapi pasangan versi 17→18 — dipakai sebagai konteks historis (kolisi `account_payment.amount_paid` sudah ada sejak dulu), BUKAN entry 18→19. | `migration-tool/knowledge/dependency-compat/` |

Tidak ada entry `dependency-compat` untuk pasangan 18.0→19.0 sama sekali — project ini adalah **project migrasi 18→19 pertama** lewat `migration-tool`. Temuan baru di bawah dicatat ke `migration-records/` (§3), sesuai proses.

## 0b. Gate Community vs Enterprise

- [x] Dependency map `01a_MIGRATION_INTAKE.md` §2 — semua 4 dependency (`base`, `sale`, `account`, `sale_management`) **Native Community**, tidak ada baris Enterprise.
- [x] Karena tidak ada dependency Enterprise, cukup `native-target` (`enterprise19.0/odoo`, bagian Community-nya) untuk analisis di bawah. `native-target-enterprise` (folder gabungan yang sama) tetap di-connect sebagai referensi per keputusan dev di `01a` §0, tapi tidak ada dependency Enterprise yang perlu dicek satu-per-satu di sini.
- [x] Investigasi di bawah (delegasi agent Explore) juga sudah grep repo-wide `enterprise19.0/odoo/addons` (yang mencakup addon Enterprise tergabung) untuk kolisi nama field/method — tidak ditemukan apa pun yang collide (lihat DIFF-04).

## 0c. Gate Transitive Dependency

- [x] Tidak ada dependency yang DIHAPUS dari `depends` di migrasi ini (semua 4: `base`/`sale`/`account`/`sale_management` tetap tersedia utuh di 19.0) — gate ini **N/A**, tidak ada transitive-dependency risk untuk dicek.

---

## 1. Perubahan Native (Core/Enterprise)

> Investigasi lengkap dijalankan lewat agent riset (Explore) yang membandingkan `native-source` (`D:\Kuncoro\doodex\repo\odoo18`) vs `native-target` (`D:\Kuncoro\doodex\repo\enterprise19.0\odoo`) secara langsung, file:line, untuk setiap hook/field yang dipakai atau didefinisikan modul ini. Ringkasan di bawah; detail lengkap (quote kode penuh) tersimpan di `migration-tool/migration-records/advanced_sales_analysis_18.0_19.0/SUMMARY.md`.

| ID | File/simbol modul | Simbol native terkait | Status di target | Dampak | Sumber |
|---|---|---|---|---|---|
| DIFF-01 | `models/sale_report.py:114,118` (`SaleOrderLine._compute_asa_amount_to_invoice`) — `line.tax_id.filtered(...)`, `line.tax_id.compute_all(...)` | `sale.order.line.tax_id` (`addons/sale/models/sale_order_line.py:159-165` di 18.0) | **Rename** — 19.0 me-rename field ini jadi `tax_ids` (`addons/sale/models/sale_order_line.py:162-169`, compute `_compute_tax_ids`, `store=True` — DB column ikut berubah, ORM core yang urus, bukan tanggung jawab modul). `tax_id` **tidak ada lagi** di 19.0. | **KRITIS — akan `AttributeError` saat runtime.** Karena field `store=True`, crash terjadi saat write/recompute (konfirmasi order, bukan cuma saat buka report) — bukan cuma masalah tampilan. Wajib fix Step 6 (rename ke `tax_ids` di kedua baris). | Analisis baru (agent Explore, 2026-08-26), dicek langsung `native-source`/`native-target` |
| DIFF-02 | `models/sale_report.py:9-18` (`SaleReport._select_additional_fields`, hook resmi) | `sale.report._select_additional_fields()`, `_select_sale()`, `_group_by_sale()`, `_query()`, `_with_sale()` | **Tidak berubah** — hook signature identik; `_group_by_sale()` GROUP BY list byte-for-byte identik 18.0↔19.0 (28 kolom, sudah termasuk `l.price_unit`/`l.invoice_status`/`l.is_downpayment` yang jadi baseline sejak MF-01 17→18) — TIDAK ADA pengulangan gap granularitas seperti MF-01. `_select_sale()`/`_from_sale()` me-rename kolom internal `product_uom`→`product_uom_id` (konsisten dengan rename `sale.order.line.product_uom`→`product_uom_id`) — tidak dipakai modul ini (modul cuma pakai `product_uom_qty`, tidak terdampak). | Tidak ada dampak ke modul — hook tetap kompatibel 1:1. | Analisis baru, dicek langsung |
| DIFF-03 | `models/sale_report.py:94-143` (`_compute_asa_amount_to_invoice`) — pakai `line._get_invoice_lines()`, `line.price_subtotal`, `line.qty_delivered`, `line.product_uom_qty` | `sale.order.line._get_invoice_lines()` | **Tidak berubah** (signature & return value identik untuk pemanggilan tanpa context `accrual_entry_date`, yang mana modul ini tidak pernah set) — hanya perubahan internal kosmetik (`self._context`→`self.env.context`). | Tidak ada dampak. | Analisis baru, dicek langsung |
| DIFF-04 | Semua field baru modul: `sale.order.line.amount_received`/`waiting_for_payment`/`asa_amount_to_invoice`, `account.move.amount_paid`/`amount_paid_cn`/`amount_dp`/`amount_dp2`/`amount_dp_nopaid`/`amount_dp2_nopaid`/`amount_refund`/`amount_refund_nopaid` | Grep repo-wide `enterprise19.0/odoo/addons` (Community+Enterprise tergabung) untuk field/method BARU dengan nama identik (lesson MF-02: cek arah "core menambah nama yang sama seperti modul", bukan cuma "API yang dipakai modul masih ada") | **Tidak ada kolisi baru.** `sale.order.line.amount_to_invoice` (core, `Monetary`) sudah ada sejak baseline 18.0 (MF-02 sudah menyelesaikannya via rename ke `asa_amount_to_invoice`) — 19.0 tidak mengubah/menghapus field core ini, cuma menambah field baru terpisah `amount_to_invoice_at_date` (nama beda, tidak collide). `account.move.amount_paid` (dari `account_payment`, kolisi lama `[BSL-006]`) byte-identik 18.0↔19.0 — kolisi sudah ada di baseline, TIDAK bertambah parah. | Tidak ada dampak BARU dari migrasi 18→19 (kolisi `[BSL-006]` tetap ada seperti sebelumnya, sudah diketahui & didokumentasikan sebagai behavior yang dipertahankan). | Analisis baru, dicek langsung + grep repo-wide |
| DIFF-05 | `sale.report` (UNION branch POS, tidak disentuh modul tapi relevan untuk column-count UNION) | `addons/pos_sale/report/sale_report.py` `_select_pos()` | **Tidak berubah secara struktural** — column count basis (39→40, tumbuh simetris dengan `_select_sale()` karena `currency_id` sama-sama ditambah sebagai literal SQL) tetap matched, tidak ada UNION mismatch. `pos.state`/`qty_invoiced` CASE logic direfactor (POS-side sign/invoiced-tracking fix), tidak menyentuh 3 kolom hook milik modul ini (`_fill_pos_fields()` tetap NULL-fill kolom yang tidak di-remap, sama seperti 18.0). | Tidak ada dampak — resiko UNION mismatch (pola F-19/MF-01 lama) dikonfirmasi TIDAK terulang. | Analisis baru, dicek langsung |
| DIFF-06 | `models/sale_report.py` — pakai `currency_id._convert()`, `tax_id.compute_all()` (API umum, bukan spesifik field custom) | `res.currency._convert()`, `account.tax.compute_all()` | **Tidak berubah** — signature identik di 19.0. | Tidak ada dampak. | Analisis baru, dicek langsung |

**Catatan informasional (bukan dampak ke kode modul, tapi dicatat untuk kelengkapan — lihat SUMMARY.md untuk detail):**
- `sale.report.currency_id`: di 18.0 non-stored compute (`_compute_currency_id`), di 19.0 jadi literal SQL langsung di `_select_sale()`/`_select_pos()`. Modul ini tidak override/panggil `_compute_currency_id()` sama sekali — tidak terdampak.
- `sale.report.product_uom`→`product_uom_id` (rename) dan formula arah UoM factor (`/u.factor*u2.factor` → `*u.factor/u2.factor`) di kolom qty/weight/volume `_select_sale()` — modul ini tidak menyentuh kolom-kolom itu, tidak terdampak kode. Di luar scope kode modul: kalau ada saved filter/pivot/dashboard EKSTERNAL yang merujuk nama teknis `product_uom` di `sale.report`, itu akan patah — perlu diteruskan ke business/BI owner, dicatat di `03_MIGRATION_SPEC.md` sebagai catatan non-kode.

## 2. Kompatibilitas Dependency (OCA/Third-Party)

**N/A** — tidak ada dependency OCA/third-party (dikonfirmasi dev, `01a_MIGRATION_INTAKE.md` §0/§0a).

## 3. Temuan Baru — Ditulis ke Migration Records

- [x] **DIFF-01 (`tax_id`→`tax_ids` rename)** dicatat sebagai kandidat `version-diff` baru di `migration-tool/migration-records/advanced_sales_analysis_18.0_19.0/SUMMARY.md` — genuinely general (`sale.order.line.tax_id` dipakai luas oleh modul custom apa pun yang menghitung pajak manual), dan ini pasangan versi 18→19 PERTAMA yang menemukannya lewat tool ini (belum ada di `knowledge/version-diffs/18-to-19.md` §1/§2 riset di muka).
- [x] DIFF-02 s.d. DIFF-06 (konfirmasi "tidak berubah"/"tidak ada kolisi baru") dicatat juga di `SUMMARY.md` sebagai data point `dependency-compat` (`sale_report`/`account_payment` 18→19) — melengkapi entry 17→18 yang sudah ada di `knowledge/`.
- [ ] Promosi ke `knowledge/` HANYA lewat sesi curation eksplisit (`templates/CURATION_PROMPT.md`) — tidak dilakukan di step ini.

## 4. Ringkasan Risiko

| Item | Level risiko | Catatan |
|---|---|---|
| DIFF-01 — `tax_id`→`tax_ids` | **Kritis (install/runtime-blocking)** | Wajib fix di Step 6 sebelum G1 (install test) bisa lulus — ini termasuk "wajib untuk kompatibilitas 19.0", diizinkan oleh `01a_MIGRATION_INTAKE.md`/`CLAUDE.md` §Forbidden Actions (bukan perubahan business logic). |
| DIFF-02 s.d. DIFF-06 | Rendah/Nihil | Tidak ada tindakan diperlukan — dikonfirmasi kompatibel 1:1. |
| Kolisi `account.move.amount_paid` vs `account_payment` (`[BSL-006]`) | Sedang (sudah ada sejak lama, tidak bertambah parah) | Bukan target perbaikan migrasi ini (baseline yang dipertahankan) — tetap dipantau kalau ada gate Step 8/9 yang relevan. |
| Catatan non-kode: `product_uom` rename, UoM factor formula arah | Informasional | Di luar scope kode modul — teruskan ke business/BI owner kalau ada dashboard eksternal yang bergantung nama teknis field. |
