# Diff & Compatibility Analysis — advanced_sales_analysis

**Step:** 2 — Diff & Compatibility Analysis
**Versi:** 19.0 → 20.0
**Tanggal:** 2026-09-24
**Ref:** `01_intake/01a_MIGRATION_INTAKE.md`, `migration-tool/knowledge/`
**Status:** ✅ Selesai

---

## 0. Knowledge Base Check

| Sumber | Sudah ada entry? | Lokasi |
|---|---|---|
| `version-diffs/19-to-20.md` | Ya | 6 baris (logout route, `logOutItem`, `ir.access.csv`, ACL `res.partner` self-write, `computeOptionalActiveFields`, pin pesan `mail`). **Tidak ada yang relevan** untuk modul ini (tidak ada JS, tidak ada ACL yang dimuat, tidak menyentuh `res.partner`/`mail`). Catatan infra (tidak ada image `odoo:20.0`, `down -v` sebelum G1, `--http-interface=0.0.0.0`) dipakai langsung. |
| `dependency-compat/sale_report/19-to-20.md` | **Tidak** (hanya 17→18, 18→19) | Analisis baru di §1 — kandidat entry baru (§3). |
| `dependency-compat/account_payment/19-to-20.md` | Tidak (hanya 17→18) | Analisis baru di §1 (DIFF-05). |

## 0b. Gate Community vs Enterprise

- Dependency map `01a` §2: tidak ada baris Enterprise → cukup `native-target` (`odoo20`).
- Tetap dicek `enterprise20` untuk kolisi nama field / override `sale.report` (grep `_select_dict`, nama field modul): tidak ada override `sale.report` Enterprise selain `partner_commission` (menambah field sendiri lewat `_select_dict`, tidak bentrok nama). Tidak ada field Enterprise bernama sama dengan field modul.

## 0c. Gate Transitive Dependency

Tidak ada dependency yang dihapus dari `depends`. N/A — dicek, tidak ada yang perlu ditambahkan.

## 0d. Gate Grep Rename Knowledge Base

Entry knowledge base yang relevan (`sale_report` 18→19: `tax_id`→`tax_ids`) sudah di-apply di 19.0. Grep ulang seluruh modul (`.py` termasuk `tests/`): `tax_id\b` 0 kemunculan; `tax_ids` di `sale_report.py:114,118,130,131` + `tests/test_sale_order_line.py` — nama tetap sama di 20.0 (`odoo20/addons/sale/models/sale_order_line.py` field `tax_ids`). Tidak ada rename baru.

## 0e. Gate Silent-Regression per Tipe Override

| Override | Kategori | Hasil |
|---|---|---|
| `sale.report._select_additional_fields()` | (a) Python, `super()` | **Method native DIHAPUS di 20.0** — override tetap ter-load tanpa error tapi TIDAK PERNAH dipanggil (entry point `_table_query`/`_query()` diganti `_table_sql` → `_select_dict(table)`). Silent regression → DIFF-01. |
| `account.move._compute_amount_paid` (+ field `amount_paid`) | (a) Python, TANPA `super()`, menimpa definisi `account_payment` | Entry point: `@api.depends` compute + stored field. `account_payment` 20.0 definisi identik 19.0 (Monetary non-stored dari `transaction_ids`). Tidak berubah → DIFF-05. |
| `account.move._compute_amount_dp`, `sale.order.line._compute_*` (3) | (a) method baru milik modul, bukan override | Field native yang dibaca dicek satu per satu (DIFF-03, DIFF-04). |

Tidak ada XML/Owl/registry → (b)(c)(d) N/A.

---

## 1. Perubahan Native (Core/Enterprise)

| ID | File/simbol modul | Simbol native terkait | Status di target | Dampak | Sumber |
|---|---|---|---|---|---|
| DIFF-01 | `models/sale_report.py:13-18` `SaleReport._select_additional_fields()` | `sale.report` (`odoo19/addons/sale/report/sale_report.py` `_select_sale()` + `_select_additional_fields()` string SQL, `_query()`/`_table_query`) → `odoo20/addons/sale/report/sale_report.py:123-189` (`_table_sql` property, `_select_dict(table: TableSQL)` → `dict[str, SQL]`, `_groupby_list(table)`, `_select_dict_to_list()` isi `NULL` untuk field stored yang tidak ada di dict) | **Dihapus / arsitektur diganti** | **KRITIS.** Tanpa port: 3 field `sale.report` diisi `NULL` (tipe tak bertipe → `text` di subselect). **Bukti eksekusi (probe 2026-09-24, manifest di-bump saja):** `sale.report.search()` → nilai `0.0` (test AC-07-01/01b/01c/04 FAIL `0.0 != 100.0`); pivot Sales Analysis dengan measure *Amount Received* → `psycopg2 … function sum(text) does not exist` (test browser FAIL, HTTP 500). Install TIDAK gagal — hanya ketahuan dari test nilai/pivot. Fix: override `_select_dict(table)` → `super()._select_dict(table) \| {...}` dengan `SQL("CASE WHEN %s IS NOT NULL THEN SUM(%s) ELSE 0 END", table.product_id, table.<field>)` — pola sama dengan `sale_margin`/`sale_stock` 20.0. | Analisis baru (`native-source`/`native-target` Community) + probe eksekusi |
| DIFF-02 | `sale.report` field `amount_to_invoice` (modul) | `odoo20/addons/pos_sale/report/sale_report.py:57` `_select_pos_dict()` punya key `'amount_to_invoice'` (dan `'amount_invoiced'`) — padahal `sale.report` native 20.0 tidak punya field itu. 19.0: `_fill_pos_fields()` mengisi semua additional field modul dengan `NULL` untuk cabang POS. | Behavior berubah (hanya kalau `pos_sale` terinstall) | Dengan `pos_sale` terinstall: kolom modul `amount_to_invoice` di baris POS = `(CASE WHEN account_move IS NULL THEN SUM(price_subtotal) ELSE 0 END) * rate` (19.0: `NULL`). `amount_received`/`waiting_for_payment` tetap `NULL` di baris POS (tidak ada key). UNION tetap valid (jumlah kolom ditentukan `_fields`, bukan dict) — regresi F-19 (column-count mismatch) secara struktural tidak mungkin lagi. **Keputusan dev 2026-09-24: diterima & didokumentasikan** (MF-02). | Analisis baru |
| DIFF-03 | `sale_report.py` compute `sale.order.line` — field yang dibaca: `state`, `product_id.invoice_policy`, `qty_delivered`, `product_uom_qty`, `price_unit`, `discount`, `tax_ids`, `currency_id`, `company_id`, `order_id.partner_shipping_id`, `price_subtotal`, `product_template_id`, `untaxed_amount_invoiced`, `invoice_lines`, `_get_invoice_lines()` | `odoo20/addons/sale/models/sale_order_line.py`, `product_template.py` | Tidak berubah (semantik) | Semua masih ada. Catatan: `_get_invoice_lines()` identik (hanya format); `product.template.invoice_policy` tetap selection `order`/`delivery` (compute default dari company, `readonly=False`); SOL 20.0 menambah field non-stored `invoice_policy` + depends `order_id.invoice_overages` di `qty_to_invoice` — tidak dipakai modul. `account.tax.compute_all()` signature menambah kwarg opsional `document_tax_mode` di akhir — pemanggilan modul (positional `price_unit`, kwarg `currency/quantity/product/partner`) tetap valid. `res.currency._convert()` signature sama. Terbukti: semua test AC-04/05/06 (termasuk `tax_ids` price_include) PASS di probe. | Analisis baru + probe |
| DIFF-04 | `sale_report.py` compute `account.move` — `move_type`, `payment_state`, `amount_total`, `amount_residual`, `amount_untaxed`, `invoice_line_ids`, `state`; `account.move.line` `price_subtotal`, `price_unit`, `quantity`, `discount`, `tax_ids`, `currency_id`, `date`, `product_id` | `odoo20/addons/account/models/account_move.py` | Tidak berubah | `PAYMENT_STATE_SELECTION` identik 19↔20 (`not_paid, in_payment, paid, partial, reversed, blocked, invoicing_legacy`). Semua test AC-02/03 PASS di probe. | Analisis baru + probe |
| DIFF-05 | `account.move.amount_paid` / `_compute_amount_paid` (kolisi BSL-006) | `odoo20/addons/account_payment/models/account_move.py:25-49` | Tidak berubah | Definisi `account_payment` 20.0 identik 19.0 (Monetary, non-stored, `transaction_ids` authorized/done). Diff file hanya di bagian lain (`get_bool`, rename variabel portal). Kolisi & pemenang MRO tetap sama — test AC-01-03 (3 test) PASS di probe. | Analisis baru + probe |
| DIFF-06 | Granularitas `sale.report` (BSL-023 poin 2) | `_group_by_sale()` 19.0 → `_groupby_list()` 20.0 | Behavior core berubah | 20.0 menambah `l.name` (deskripsi baris SO) dan `l.product_uom_id` ke GROUP BY, dan field baru `line_name`; kolom `s.*`/`partner.*` tidak lagi di GROUP BY eksplisit (diambil via `order_id`/`partner_id` yang sudah di-group). Efek: 2 baris SO produk & harga sama tapi deskripsi beda → 2 baris laporan (19.0: 1). Modul tidak meng-override GROUP BY — otomatis ikut core (preseden MF-01 17→18, disetujui pemilik modul). Nilai total measure tidak berubah, hanya granularitas baris. `test_ac_07_03` (harga beda → 2 baris) tetap PASS di probe. Dicatat MF-03. | Analisis baru + probe |
| DIFF-07 | `__manifest__.py` `version: 19.0.1.0.0` | `odoo20/odoo/modules/module.py:500-501` `check_version` | Wajib bump | Versi 19.0 → `WARNING … incompatible version, setting installable=False` → modul tidak terinstall dan test run `0 failed, 0 error(s) of 0 tests` (sukses palsu). **Bukti probe 1 (2026-09-24).** | Probe |
| DIFF-08 | `security/ir.model.access.csv` (tidak dimuat) | 20.0 `ir.access.csv` menggantikan `ir.model.access.csv` (knowledge 19-to-20) | Tidak berdampak | File tidak ada di `data` manifest (baris di-comment, BSL-015) → tidak pernah di-load, jadi perubahan format tidak berpengaruh. Dipertahankan apa adanya. | Knowledge base |
| DIFF-09 | Manifest keys `images`, `price`, `currency`, `company`, `author` | `odoo20/odoo/modules/module.py` `_DEFAULT_MANIFEST` | Tidak berubah | Key non-standar (`company`) tetap diabaikan seperti di 19.0; `images` masih didukung. Update `images` → `banner.gif`+`icon.png` = keputusan dev (aset store), bukan kompatibilitas. | Analisis baru |
| DIFF-10 | Test infra: `TestSaleCommon`, `partner_a`, `account.payment.register`, `HttpCase.browser_js`, `/web#action=`, xmlid `sale.action_order_report_all`, selector pivot (`.o_pivot_buttons`, `button.o_switch_view.o_pivot`, `.o-dropdown--menu`) | `odoo20/addons/sale/tests/common.py`, `odoo/tests/common.py:2877`, `web/static/src/views/pivot/*` | Tidak berubah | Semua ada; test browser di probe berhasil membuka pivot & dropdown Measures (gagal hanya karena DIFF-01). | Analisis baru + probe |

**Kolisi arah sebaliknya (field/method BARU core bernama sama dengan milik modul):** grep `odoo20/addons` + `enterprise20` untuk `amount_received`, `waiting_for_payment`, `asa_amount_to_invoice`, `amount_paid_cn`, `amount_dp*`, `amount_refund*`, dan nama 4 method compute modul → **0 kemunculan** di model yang di-inherit modul. `amount_paid` di `sale.order` (Float, sudah ada di 19.0) dan `pos.order` — model lain, tidak bentrok. `sale.order.line.amount_to_invoice` (sejak 18.0) — sudah ditangani MF-02 17→18 (`asa_` prefix).

## 2. Kompatibilitas Dependency (OCA/Third-Party)

Tidak ada dependency OCA/third-party. N/A.

## 3. Temuan Baru — Migration Records

- [x] Kandidat `dependency-compat/sale_report/19-to-20.md` (DIFF-01, DIFF-02, DIFF-06) dan `dependency-compat/account_payment/19-to-20.md` (DIFF-05 stabil) → dicatat di `migration-tool/migration-records/advanced_sales_analysis_19.0_20.0/SUMMARY.md`.
- [x] Kandidat `version-diffs/19-to-20.md`: pola umum "hook SQL string report (`_select_additional_fields`/`_select_*`/`_from_*`/`_group_by_*`) diganti `_table_sql`/`_select_dict(TableSQL)` → override lama silent; kolom tanpa nilai jadi `NULL` bertipe text → `SUM(text)` crash di pivot" → SUMMARY.md.
- [x] Tidak ada penulisan langsung ke `knowledge/`.

## 4. Ringkasan Risiko

| Item | Level risiko | Catatan |
|---|---|---|
| DIFF-01 `_select_additional_fields` dihapus | **Kritis** | Port ke `_select_dict`, satu cara benar. Verifikasi wajib lewat nilai (AC-07) + pivot browser, bukan install. |
| DIFF-07 manifest version | Tinggi (install-blocking, sukses palsu) | Bump `20.0.1.0.0`. |
| DIFF-02 POS `amount_to_invoice` | Rendah (hanya dengan `pos_sale`, di luar dependency) | Diterima dev, MF-02. |
| DIFF-06 granularitas GROUP BY core | Rendah | Core behavior, total tidak berubah, MF-03. |
| DIFF-03/04/05/08/09/10 | Tidak ada | Stabil, dibuktikan probe. |
