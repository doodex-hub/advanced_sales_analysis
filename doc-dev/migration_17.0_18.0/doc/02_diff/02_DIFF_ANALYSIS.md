# Diff & Compatibility Analysis — advanced_sales_analysis

**Step:** 2 — Diff & Compatibility Analysis
**Versi:** 17.0 → 18.0
**Tanggal:** 2026-08-21
**Ref:** `01_intake/01a_MIGRATION_INTAKE.md`, `01_intake/01b_BASELINE_SPEC.md`, `migration-tool/knowledge/`

---

## 0. Knowledge Base Check

| Sumber | Sudah ada entry? | Lokasi |
|---|---|---|
| `version-diffs/17-to-18.md` | Ya | Dibaca penuh — §1 (API/behavior high-confidence), §1b/§1c (pengalaman migrasi nyata modul lain). Sebagian besar item (view `<tree>`→`<list>`, chatter, kanban, Owl/JS, `useService("rpc")`) **tidak relevan** ke modul ini karena modul ini tidak punya view/XML/JS sama sekali (lihat `01a_MIGRATION_INTAKE.md` §2b). Item yang relevan: `group_operator`→`aggregator` (dicek §1 di bawah, tidak berdampak), `@api.depends` completeness (relevan ke `[BSL-021]`, dicatat sebagai risiko re-verify Step 9). |
| `dependency-compat/<nama>/...` | Tidak ada entry untuk `sale`/`account`/`sale_management`/`account_payment` | — analisis baru ditulis di §1 di bawah, kandidat entry baru dicatat di §3 |

## 0b. Gate Community vs Enterprise

- [x] Dibaca ulang `01a_MIGRATION_INTAKE.md` §2 — **TIDAK ADA** baris "Native Enterprise". Keempat dependency (`base`, `sale`, `account`, `sale_management`) semuanya Native Community.
- [x] Karena tidak ada Enterprise → lanjut §1 cukup dengan `native-target` (Community, `D:\Kuncoro\doodex\repo\odoo18`, branch `18.0` diverifikasi). `native-target-enterprise` tidak di-connect, tidak relevan.
- Kolom "Sumber" tiap baris `DIFF-NNN` di §1 di bawah eksplisit menyebut `native-target`/`native-source` (Community, tidak ada baris Enterprise sama sekali di dokumen ini).

## 0c. Gate Transitive Dependency

- **N/A — tidak ada dependency yang dihapus dari `depends`.** Keempat dependency (`base`, `sale`, `account`, `sale_management`) dikonfirmasi ADA di `native-target` 18.0 (lihat `01a_MIGRATION_INTAKE.md` §2) — tidak ada yang perlu dihapus, jadi tidak ada risiko transitif-dependency-hilang seperti kasus `sale_product_configurator` di `purchase_product_optional`.

---

## 1. Perubahan Native (Core/Enterprise)

Modul ini tidak punya view/XML/JS/controller aktif (lihat `01a_MIGRATION_INTAKE.md` §2b) — seluruh permukaan ketergantungan ke native adalah **API Python murni** (method override/hook, field yang dibaca lewat `@api.depends`, field yang di-`_inherit`). Tidak ada pola `<xpath>`/`t-call` untuk dicek.

| ID | File/simbol modul | Simbol native terkait | Status di target | Dampak | Sumber |
|---|---|---|---|---|---|
| DIFF-01 | `models/sale_report.py:13-18` — `SaleReport._select_additional_fields()` (override, panggil `super()`) | `sale.report._select_additional_fields()` + `_select_sale()` (baris 164/175, `addons/sale/report/sale_report.py`) — hook yang merangkai hasilnya jadi `%s AS %s` di SELECT | **Hook `_select_additional_fields()` sendiri tidak berubah** — struktur/nama method identik 17.0↔18.0. **KOREKSI (2026-08-21, setelah eksekusi G1 — lihat `FINDINGS.md` MF-01): analisis awal baris ini TIDAK LENGKAP.** Awalnya cuma dicek alias tabel currency (`currency_table`→`account_currency_table`) dan disimpulkan "modul tidak override `_group_by_sale()`, jadi tidak terdampak" — **kesimpulan itu salah**. Isi kolom `_group_by_sale()` core sendiri BERUBAH signifikan 18.0: menambah `l.price_unit`, `l.invoice_status`, `l.is_downpayment`; menghapus `s.analytic_account_id`. Karena modul ini memakai GROUP BY bawaan core apa pun isinya (tidak override), perubahan granularitas ini **terbawa otomatis** ke laporan modul — dikonfirmasi eksekusi nyata (`test_ac_07_03_group_by_tidak_lagi_memecah_baris` FAIL, `2 != 1`). Ini genuinely gap migrasi (`[GAP-MIGRASI]`), bukan sekadar catatan info. | **Tinggi — lihat `FINDINGS.md` MF-01 untuk analisis dampak & opsi keputusan.** `[BSL-005]` (mekanisme hook) tetap valid, TAPI `[BSL-023]` (granularitas laporan "sama seperti core") TIDAK bisa diklaim identik 17.0↔18.0 lagi — core sendiri yang berubah. | `native-target` 18.0 + `native-source` 17.0, `_group_by_sale()` dibandingkan KOLOM-PER-KOLOM (bukan cuma nama method) — pelajaran: perbandingan awal Step 2 kurang dalam, cukup cek existence/struktur method, tidak membandingkan isi list argumen/kolom secara eksplisit |
| DIFF-02 | `models/sale_report.py:22-41` — `AccountMove.amount_paid`/`_compute_amount_paid` (nama field & method PERSIS sama dengan core) | `account_payment` (Community, `auto_install: ['account']`) — `account.move.amount_paid` (`Monetary`, `compute='_compute_amount_paid'`, `@api.depends('transaction_ids')`) | **Tidak berubah — kolisi tetap ada identik.** Dicek langsung `account_payment/models/account_move.py` di `native-target` 18.0: definisi field, tipe (`Monetary`), method, dan `@api.depends` byte-identik dengan 17.0. `auto_install: ['account']` tidak berubah. | Kolisi F-01/`[BSL-006]` **terbawa 1:1 ke 18.0, tidak membaik maupun memburuk** — tetap harus dipertahankan apa adanya sesuai baseline (bug-compatible), MRO/urutan load registry tetap menentukan siapa yang menang. | `native-target` 18.0 + `native-source` 17.0, `account_payment/models/account_move.py` dibandingkan langsung |
| DIFF-03 | `models/sale_report.py:94-135` (`SaleOrderLine._compute_amount_to_invoice`, logic yang di-copy sebagian dari core) | `sale.order.line._compute_untaxed_amount_to_invoice()` (`addons/sale/models/sale_order_line.py:1086` di 18.0 / `:872` di 17.0) | **Tidak berubah — byte-identical.** Dibandingkan baris-per-baris: guard `state`, kalkulasi `uom_qty_to_consider`/`price_reduce`/`price_subtotal`, cabang `tax_id.filtered(price_include)`, cabang re-invoicing beda discount — semuanya sama persis di 17.0 dan 18.0 (cuma nomor baris file yang beda). | Tidak ada dampak baru dari sisi core. `[BSL-008]` (F-17, dead-code `invoice_policy` di cabang `else`) tetap ada persis sama di 18.0 — bug yang harus dipertahankan, bukan otomatis membaik karena core tidak berubah. | `native-target` 18.0 + `native-source` 17.0, `sale/models/sale_order_line.py` |
| DIFF-04 | `models/sale_report.py` — pemakaian `line._get_invoice_lines()`, `line.is_downpayment` (disebut di rekomendasi F-04, belum dipakai modul), `line.qty_delivered`, `line.product_id.invoice_policy` | `sale.order.line._get_invoice_lines()`, field `is_downpayment` (`addons/sale/models/sale_order_line.py`) | **Tidak berubah** — kedua simbol dikonfirmasi ADA di 18.0 dengan nama sama (`_get_invoice_lines` baris 972 di 18.0/781 di 17.0; `is_downpayment` field Boolean ada di kedua versi). | Tidak ada dampak — modul aman memanggil symbol ini di 18.0 tanpa perubahan. | `native-target` 18.0 + `native-source` 17.0 |
| DIFF-05 | Field definisi modul sendiri (`amount_received`, `amount_to_invoice`, `waiting_for_payment` di `sale.report`/`sale.order.line`) — tidak pakai atribut `group_operator`/`aggregator` sama sekali | Konvensi core 18.0: atribut `group_operator` (17.0) di-rename `aggregator` (18.0) — dikonfirmasi core `sale.report`/`sale.order.line` 18.0 sudah pakai `aggregator=` (mis. `price_unit`, `discount`) | **Tidak berlaku ke modul ini** — field modul sendiri tidak pernah men-set `group_operator` maupun `aggregator` (default Odoo, `SUM` untuk numeric), jadi tidak ada atribut usang untuk di-rename. | Tidak ada aksi diperlukan. Dicatat di sini supaya jelas SUDAH dicek, bukan terlewat. | `native-target` 18.0, `sale/report/sale_report.py` + `sale/models/sale_order_line.py` |
| DIFF-06 | `[BSL-021]` — `@api.depends` melingkar antar `amount_to_invoice`/`waiting_for_payment`/`amount_received` di `sale.order.line` (`models/sale_report.py:88-90`) | Perilaku ORM `@api.depends`/compute invalidation 18.0 | **Belum bisa dipastikan tanpa eksekusi.** Knowledge base umum (`version-diffs/17-to-18.md` §1b) mencatat 18.0 "lebih ketat" soal `@api.depends` tidak lengkap, TAPI terverifikasi (`library_loan`, dry run 2026-07-21) itu cuma bikin nilai diam-diam stale, BUKAN hard error/registry rejection — kasus itu beda dari `@api.depends` MELINGKAR (bukan tidak lengkap). Backfill 17.0 sudah membuktikan lewat eksekusi bahwa circular depends ini TIDAK menyebabkan registry menolak modul dan tidak ada order-dependency teramati (`test_ac_06_05...`). Diasumsikan behavior yang sama berlaku di 18.0 (mekanisme dependency graph ORM tidak termasuk dalam daftar perubahan besar 17→18 manapun yang ditemukan di riset), TAPI **wajib di-re-run test yang sama di Step 9 (Dev Testing) terhadap instance 18.0 sungguhan** sebelum dianggap pasti — jangan diasumsikan dari riset statis saja untuk item yang sifatnya runtime-dependent seperti ini. | Risiko Rendah (konsisten dengan `[BSL-021]`), tapi status "belum pasti" WAJIB dibawa ke `05a_MIGRATION_ACCEPTANCE_CRITERIA.md`/`09_DEV_TESTING.md` sebagai AC yang re-run test lama terhadap 18.0, bukan diasumsikan lolos begitu saja. | `version-diffs/17-to-18.md` §1b (riset umum) — TIDAK ada verifikasi langsung khusus circular-depends di 18.0, ini gap yang eksplisit dicatat, bukan disembunyikan |

## 2. Kompatibilitas Dependency (OCA/Third-Party)

**N/A — tidak ada dependency OCA/third-party.** Semua dependency (`base`, `sale`, `account`, `sale_management`) Native Community, dicek langsung di §1 di atas.

## 3. Temuan Baru — Kandidat untuk `migration-records/`

Dicatat sebagai kandidat di `migration-tool/migration-records/advanced_sales_analysis_17.0_18.0/SUMMARY.md` (belum ditulis — akan dibuat sebelum Step 2 ditutup), BUKAN langsung ke `knowledge/`:

- **Kategori `dependency-compat/account_payment`:** `account.move.amount_paid`/`_compute_amount_paid` (Monetary, `@api.depends('transaction_ids')`, `auto_install` bareng `account`) byte-identik 17.0↔18.0 — dependency-compat entry baru yang berguna untuk modul migrasi LAIN yang mungkin punya kolisi nama field serupa dengan `account_payment`.
- **Kategori `dependency-compat/sale` (spesifik `sale.order.line`):** `_compute_untaxed_amount_to_invoice()`, `_get_invoice_lines()`, field `is_downpayment` — semuanya byte-identik 17.0↔18.0. Berguna sebagai referensi cepat untuk modul lain yang extend `sale.order.line` di area invoicing/down-payment.
- **Kategori `version-diff` (general, tambahan ke `17-to-18.md`):** alias tabel currency di `sale.report._group_by_sale()` berubah nama (`currency_table`→`account_currency_table`) — item kecil, tidak breaking untuk modul ini, tapi berguna dicatat untuk modul lain yang MASIH override `_group_by_sale()` secara manual (tidak seperti modul ini yang sudah pindah ke `_select_additional_fields()`).

## 4. Ringkasan Risiko

| Item | Level risiko | Catatan |
|---|---|---|
| DIFF-02 — Kolisi `amount_paid` dengan `account_payment` | **Tinggi** (carried over, tidak berubah dari 17.0) | Bukan risiko BARU dari migrasi — sudah ada di baseline 17.0 (F-01), dipertahankan sesuai prinsip migrasi identik. Tetap ditandai Tinggi karena dampak nyata (portal pembayaran) kalau pemilik modul suatu saat memutuskan sebaliknya. |
| DIFF-03 — Dead-code `invoice_policy` di `_compute_amount_to_invoice` | **Tinggi** (carried over) | Sama seperti di atas — F-17/`[BSL-008]`, bug yang harus dipertahankan, core tidak berubah jadi tidak ada "perbaikan gratis" dari migrasi. |
| DIFF-06 — `@api.depends` melingkar, belum di-re-test di 18.0 sungguhan | **Rendah, tapi status verifikasi belum pasti** | Wajib jadi item eksplisit di `05a_MIGRATION_ACCEPTANCE_CRITERIA.md`/`09_DEV_TESTING.md` — re-run `test_ac_06_05_urutan_pembacaan_field_melingkar` (atau setara) terhadap instance 18.0. |
| DIFF-01, DIFF-04, DIFF-05 | **Tidak ada risiko** | Hook/API/field yang dipakai modul dikonfirmasi stabil 17.0↔18.0. |
| Area di luar scope modul ini (view `<tree>`, chatter, Owl/JS, `useService`) | **N/A** | Modul tidak punya view/XML/JS — seluruh kelas risiko ini dari `version-diffs/17-to-18.md` tidak berlaku. |

**Kesimpulan Step 2:** Tidak ditemukan breaking change yang memaksa perubahan kode untuk migrasi murni port (semua API/hook yang dipakai modul stabil 17.0→18.0). Risiko yang ada (DIFF-02, DIFF-03) adalah bug pre-existing yang **sengaja dipertahankan**, bukan sesuatu yang perlu "diperbaiki karena migrasi" — konsisten `01a_MIGRATION_INTAKE.md` §5 (Scope Boundary). Satu item (DIFF-06) statusnya "kemungkinan besar aman, tapi wajib re-verify eksekusi" — dibawa eksplisit ke Step 5/9, bukan diasumsikan selesai.
