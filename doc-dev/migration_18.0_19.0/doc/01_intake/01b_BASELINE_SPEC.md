# Baseline Spec — advanced_sales_analysis

**Step:** 1 — Intake & Scope (pelengkap `01a_MIGRATION_INTAKE.md`)
**Tujuan:** dokumentasikan APA yang modul lakukan (behavior as-is) di **18.0** — sumber kebenaran untuk `05a_MIGRATION_ACCEPTANCE_CRITERIA.md` dan semua testing migrasi 18→19 (step 9/10/11).
**Tanggal:** 2026-08-26
**Sumber:** Direkonsiliasi dari `doc-dev/migration_17.0_18.0/doc/01_intake/01b_BASELINE_SPEC.md` (baseline 17.0, `BSL-NNN`) + `doc-dev/migration_17.0_18.0/doc/FINDINGS.md` (MF-01, MF-02 — dua gap migrasi 17→18, KEDUANYA sudah RESOLVED dan sekarang bagian dari baseline 18.0) + cross-check langsung ke kode `advanced_sales_analysis/models/sale_report.py` di `source-codebase`/`target-codebase` saat ini (branch `migration/18.0_target`, dibaca 2026-08-26).

> Semua klaim di bawah dicross-check ulang terhadap kode aktual (dibaca 2026-08-26) — cocok 100%, tidak ditemukan penyimpangan baru. Karena itu semua diberi tag `[MATCH]`. ID `BSL-NNN` KARENA melanjutkan skema project sebelumnya (bukan direset) — nomor yang sama menunjuk klaim yang sama, dengan isi diperbarui merefleksikan baseline 18.0 (bukan 17.0) di tempat yang relevan (ditandai eksplisit di teks).

---

## Provenance Tag

`[MATCH]`/`[GAP]`/`[NO-SPEC]` — standar skema `migration-tool`. `(ref: BSL-NNN 17→18)` menunjuk ID yang sama di dokumen baseline migrasi sebelumnya; `(ref: MF-NN)` menunjuk finding migrasi 17→18 yang sudah resolved dan sekarang jadi bagian baseline ini.

---

## Ringkasan untuk Review — Perlu Konfirmasi User

**Tally:** 23 `[BSL-NNN]`, semua `[MATCH]` (0 `[GAP]`, 0 `[NO-SPEC]`) — baseline 17.0 sumbernya sudah execution-verified, dan 2 penyimpangan yang muncul saat migrasi 17→18 (MF-01, MF-02) sudah disetujui pemilik modul dan diverifikasi eksekusi (38/38 test), sekarang jadi bagian resmi baseline 18.0 tanpa ambiguitas tersisa.

1. **`[BSL-006]` (ref BSL-006 17→18):** `account.move.amount_paid` + `_compute_amount_paid` **masih** bertabrakan nama field DAN method dengan modul core `account_payment` (`auto_install` bareng `account`) — belum pernah diselesaikan (F-01 asli, dari `doc-dev-backfill`, sampai sekarang tidak dieksekusi). Behavior ini HARUS dipertahankan identik di 19.0 kecuali pemilik modul memutuskan sebaliknya. **Wajib dicek ulang di Step 2** apakah definisi core `account_payment.amount_paid` berubah di 19.0 (bisa mengubah karakter collision, seperti yang terjadi pada `amount_to_invoice` saat migrasi 17→18/MF-02).
2. **`[BSL-008]` (ref BSL-008 17→18, field DIPERBARUI ke `asa_amount_to_invoice`):** field & method sudah di-rename dari `amount_to_invoice`/`_compute_amount_to_invoice` menjadi `asa_amount_to_invoice`/`_compute_asa_amount_to_invoice` (MF-02, migrasi 17→18) untuk menghindari kolisi dengan field BARU core `sale.order.line.amount_to_invoice` (Monetary) yang lahir di 18.0. Nama BARU ini (`asa_amount_to_invoice`) adalah baseline final — TIDAK di-revert ke nama lama. Dead-code path lama (pakai `line.price_subtotal` mentah, bukan variabel lokal yang sudah mempertimbangkan `invoice_policy`/pajak) **masih ada**, dipertahankan apa adanya.
3. **`[BSL-023]` (ref BSL-023 17→18, MF-01, MF-02):** baseline 18.0 = source POST kedua fix migrasi 17→18. Granularitas `sale.report` GROUP BY mengikuti kolom core 18.0 (bukan core 17.0) — modul ini TIDAK override `_group_by_sale()`, jadi otomatis ikut apa pun granularitas core saat ini. **Wajib dicek ulang Step 2**: apakah core 19.0 mengubah lagi kolom `_group_by_sale()`/`_select_additional_fields()` dibanding 18.0 (pola yang sama seperti MF-01 bisa terulang).
4. **Field baru core yang perlu dicek arah SEBALIKNYA di Step 2 (lesson MF-02):** bukan cuma "apakah hook yang dipakai modul masih stabil", tapi "apakah core 19.0 menambah field/method BARU di `sale.order.line`/`account.move`/`sale.report` dengan nama yang SAMA seperti yang modul ini definisikan (`amount_received`, `waiting_for_payment`, `asa_amount_to_invoice`, `amount_paid`, `amount_paid_cn`, `amount_dp*`, `amount_refund*`)". Checklist ini WAJIB dijalankan Step 2 (bukan ditunda ke Step 8 seperti kejadian MF-02).
5. **15 finding kecil/quirk lain** (§8) tetap terbuka, diperlakukan sebagai behavior yang harus identik di 19.0 — bukan target perbaikan migrasi ini kecuali pemilik modul minta eksplisit.

---

## 1. Tujuan Modul

Modul memperkaya laporan **Sales Analysis** (`sale.report`) Odoo dengan tiga metrik finansial yang tidak ada di core: **Amount Received** (uang yang benar-benar sudah diterima per baris penjualan), **Waiting for Payment** (nilai yang sudah difakturkan tapi belum dibayar), dan **Amount To Invoice** (sisa yang belum difakturkan sama sekali, field internal `asa_amount_to_invoice` di `sale.order.line` — lihat `[BSL-008]`).

Karena `sale.report` adalah SQL view (`_auto=False`) yang membaca langsung tabel `sale_order_line`, ketiga metrik itu dihitung lebih dulu sebagai field stored-compute di `sale.order.line`, lalu ditarik ke SQL view lewat hook resmi `_select_additional_fields()`. Perhitungannya bertumpu pada delapan field pembantu stored-compute di `account.move` yang memecah nilai faktur ke komponen dibayar/belum dibayar/uang muka/retur.

Tujuan bisnis: menjawab "dari nilai order ini, berapa yang sudah jadi uang masuk, berapa yang masih menunggu bayar, dan berapa yang belum ditagih" langsung di pivot Sales Analysis, termasuk penanganan uang muka (down payment) dan credit note.

## 2. Model & Tanggung Jawab

| Model | Tanggung Jawab |
|---|---|
| `sale.report` (`_inherit`) | SQL view laporan penjualan. Tambah 3 kolom aggregat read-only lewat `_select_additional_fields()`. |
| `account.move` (`_inherit`) | Tambah 8 field stored-compute yang memecah nilai faktur ke komponen dibayar/belum-dibayar/uang-muka/retur — sumber data untuk compute di `sale.order.line`. |
| `sale.order.line` (`_inherit`) | Tambah 3 field stored-compute (`amount_received`, `waiting_for_payment`, `asa_amount_to_invoice`) — metrik utama yang ditarik `sale.report`. |

Tidak ada model baru (`_name`). Tidak ada view/XML (`'data': []`).

## 3. Field dengan Makna Bisnis

### `sale.report`
- `amount_received` (Float, readonly) — `SUM` dari `sale.order.line.amount_received` per grup laporan.
- `amount_to_invoice` (Float, readonly) — nama field LEVEL LAPORAN tidak berubah (tidak collide dengan apa pun di `sale.report`), sumbernya `SUM(l.asa_amount_to_invoice)`.
- `waiting_for_payment` (Float, readonly) — `SUM` dari `sale.order.line.waiting_for_payment`.

### `account.move`
- `amount_paid` / `amount_paid_cn` (Float, compute, store) — total dibayar untuk invoice/credit-note. **Masih berkolisi nama dengan `account_payment`** (`[BSL-006]`).
- `amount_dp` / `amount_dp2` / `amount_dp_nopaid` / `amount_dp2_nopaid` (Float, compute, store) — komponen uang muka (positif/negatif) × (sudah/belum dibayar).
- `amount_refund` / `amount_refund_nopaid` (Float, compute, store) — komponen retur uang muka × (sudah/belum dibayar).

### `sale.order.line`
- `amount_received` (Float, compute, store) — nilai baris SO yang sudah dibayar.
- `waiting_for_payment` (Float, compute, store) — nilai baris SO yang sudah difaktur tapi belum dibayar.
- `asa_amount_to_invoice` (Float, compute `_compute_asa_amount_to_invoice`, store) — sisa nilai baris SO yang belum difaktur. **Nama field & method SUDAH di-namespace** (`asa_` prefix) sejak migrasi 17→18 (MF-02) — bukan `amount_to_invoice` lagi.

## 4. Business Workflow (User Stories)

- `[BSL-001]` `[MATCH]` Sales manager membuka **Sales → Reporting → Sales Analysis**, menambah measure *Amount Received* untuk tahu kas yang benar-benar sudah diterima per produk/order.
- `[BSL-002]` `[MATCH]` Finance menambah measure *Waiting for Payment* untuk memisahkan nilai yang sudah ditagih tapi belum dibayar.
- `[BSL-003]` `[MATCH]` Finance menambah measure *Amount To Invoice* untuk tahu sisa nilai order yang masih harus difakturkan.
- `[BSL-004]` `[MATCH]` Baris "Down payment" dan pengurangnya tidak boleh menggandakan/menghilangkan angka di ketiga metrik (lihat `[BSL-013]` soal cara deteksinya).

Tidak ada state-transition/action button/wizard.

## 5. Server-Side Logic dengan Side Effect

- `[BSL-005]` `[MATCH]` `sale.report` mendapat 3 kolom lewat `_select_additional_fields()`: `res['amount_received']`, `res['waiting_for_payment']`, `res['amount_to_invoice']` (sumber SQL: `l.asa_amount_to_invoice`) — masing-masing `SUM(l.<kolom>)` dengan guard `CASE WHEN l.product_id IS NOT NULL THEN ... ELSE 0 END`.
  **Lokasi:** `advanced_sales_analysis/models/sale_report.py:9-18`

- `[BSL-006]` `[MATCH]` `account.move._compute_amount_paid`: untuk `out_refund` ber-`payment_state in ('paid','in_payment','partial')` → `amount_paid_cn = amount_total - amount_residual`; untuk `out_invoice` kondisi sama → `amount_paid = amount_total - amount_residual`. Tidak ada cabang `else`. **Kolisi nama field DAN method dengan core `account_payment` MASIH ADA** di baseline 18.0 (belum pernah diperbaiki) — modul ini menang di MRO (depends langsung ke `account`, load setelahnya).
  **Lokasi:** `advanced_sales_analysis/models/sale_report.py:24-41`

- `[BSL-007]` `[MATCH]` `account.move._compute_amount_dp` mengisi 6 field uang-muka, di-reset `0.0` tiap iterasi. Penugasan pakai `=` (bukan `+=`) di dalam loop — kalau >1 baris DP kategori sama per faktur, hanya baris terakhir yang menang.
  **Lokasi:** `advanced_sales_analysis/models/sale_report.py:44-83`

- `[BSL-008]` `[MATCH]` `sale.order.line._compute_asa_amount_to_invoice` (method & field di-rename dari `_compute_amount_to_invoice`/`amount_to_invoice`, MF-02): untuk baris `state in ('sale','done')`, hitung `price_subtotal` lokal mempertimbangkan `invoice_policy`/pajak `price_include`. **Cabang normal (mayoritas kasus) TETAP memakai FIELD `line.price_subtotal`, BUKAN variabel lokal** yang sudah dihitung — dead-code path yang sama seperti baseline 17.0, TIDAK diperbaiki saat rename MF-02 (rename murni mengganti nama, tidak menyentuh logic). Untuk produk delivery-based, metrik overstated.
  **Lokasi:** `advanced_sales_analysis/models/sale_report.py:94-143`

- `[BSL-009]` `[MATCH]` `sale.order.line._compute_waiting_for_payment_research`: iterasi baris faktur `state != 'cancel'` dan `payment_state in ('not_paid','partial')` → akumulasi `fixed_waiting_for_payment`, gross-up `dp_proportion` kalau ada baris DP. `@api.depends` sekarang mereferensikan `asa_amount_to_invoice` (bukan `amount_to_invoice`) — konsisten rename MF-02.
  **Lokasi:** `advanced_sales_analysis/models/sale_report.py:149-192`

- `[BSL-010]` `[MATCH]` `sale.order.line._compute_amount_received_research`: pola simetris `[BSL-009]`, iterasi baris faktur `payment_state in ('paid','in_payment','partial')`, akumulasi `fix_amount_received` pakai `move.amount_paid`/`amount_paid_cn` — bergantung ke field yang berkolisi dengan `account_payment` (`[BSL-006]`).
  **Lokasi:** `advanced_sales_analysis/models/sale_report.py:198-238`

- `[BSL-011]` `[MATCH]` Perlakuan `payment_state == 'partial'` tidak konsisten antar 4 method (3 menghitung `'partial'`, `_compute_amount_dp` tidak) — sama seperti baseline 17.0, belum diperbaiki.

- `[BSL-012]` `[MATCH]` Tidak berlaku (historis, versi backfill awal yang override `_group_by_sale()` sudah dihapus total sebelum 17.0 dijadikan source migrasi — lihat `[BSL-023]`).

## 6. Client-Side Behavior

**N/A.** Tidak ada view/XML, controller aktif, atau asset/JS/Owl. Ketiga field `sale.report` muncul otomatis sebagai *Measures* di pivot/graph.

## 7. Dependency Eksternal

### Eksplisit (manifest)
`depends: ['base', 'sale', 'account', 'sale_management']` — keempatnya Native Community, dikonfirmasi tersedia di 19.0 lewat `native-target` (`enterprise19.0`, lihat `01a_MIGRATION_INTAKE.md` §0/§2). Detail diff isi hook: `02_DIFF_ANALYSIS.md` (Step 2).

### Implisit/Inferred
- `account_payment` (Native Community, `auto_install: ['account']`) — kolisi `[BSL-006]`, masih terbuka.
- `point_of_sale` (Native Community, kalau terinstall) — berbagi hook `_select_additional_fields()` lewat `_select_pos()`.
- Instance produksi dev berjalan **Odoo Enterprise** (dikonfirmasi dev, 2026-08-26) — modul ini sendiri tidak depend Enterprise, tapi `sale.report`/`account.move` bisa saja sudah di-extend modul Enterprise lain di runtime. Belum ada bukti konkret kolisi (`native-*-enterprise` di-connect sebagai referensi, dicek lebih lanjut kalau Step 2/8 menemukan indikasi).

## 8. Quirk / Behavior Non-Obvious

- `[BSL-013]` `[MATCH]` Deteksi baris uang muka di 9 tempat memakai perbandingan nama produk ke string literal `"Down payment"` — bukan field resmi `is_downpayment`. Prioritas Tinggi, belum diperbaiki.
- `[BSL-014]` `[MATCH]` 3 kolom baru `sale.report` tidak dikonversi mata uang. Prioritas Sedang.
- `[BSL-015]` `[MATCH]` `security/ir.model.access.csv` ada secara fisik tapi entrinya di-comment di manifest, merujuk model yang tidak pernah didefinisikan. Prioritas Sedang.
- `[BSL-016]` `[MATCH]` `controllers/controllers.py` kosong tapi tetap di-import. Prioritas Rendah.
- `[BSL-017]` `[MATCH]` Label field (`string=`) salah/duplikat — 4 field `account.move` semua `string='amount dp'`; `sale.order.line.amount_received` string `'Amount Received'` (OK), TAPI `asa_amount_to_invoice` masih `string='Amount Received'` (label SALAH, warisan dari sebelum rename MF-02 — rename cuma mengubah nama teknis field, tidak menyentuh `string=`). Odoo mencatat WARNING "same label" saat instalasi. Prioritas Rendah tapi permukaan UI luas.
- `[BSL-018]` `[MATCH]` File verifikasi Google Search Console (`googleaeed8a7b9ec156e7.html`) ikut ter-commit di dalam folder addon.
- `[BSL-019]` `[MATCH]` `self.env['account.move.line'].search(...)` dipanggil di dalam loop bersarang di 2 method compute — berisiko lambat di database besar.
- `[BSL-020]` `[MATCH]` Faktur ber-`amount_untaxed == 0` selalu berkontribusi `0` ke metrik.
- `[BSL-021]` `[MATCH]` `@api.depends` melingkar antar `asa_amount_to_invoice`/`waiting_for_payment`/`amount_received`. Dampak tidak terbukti lewat eksekusi.
- `[BSL-022]` `[MATCH]` Manifest tidak punya key `assets`.
- `[BSL-023]` `[MATCH]` **State baseline 18.0 (final, hasil 2 fix migrasi 17→18):**
  1. Implementasi memakai hook resmi `_select_additional_fields()` (bukan override `_select_sale()`/`_group_by_sale()`) — sejak sebelum 17.0 dijadikan source (fix F-19, proyek `doc-dev-backfill`).
  2. **Granularitas `sale.report` GROUP BY mengikuti core 18.0** (`price_unit`, `invoice_status`, `is_downpayment` ditambahkan core, `analytic_account_id` dihapus core, dibanding core 17.0) — modul TIDAK override `_group_by_sale()` sama sekali, jadi otomatis ikut kolom apa pun yang core definisikan. **MF-01 (migrasi 17→18), disetujui pemilik modul 2026-08-21:** ini BUKAN gap yang harus "diperbaiki" balik ke granularitas 17.0 — baseline 18.0 yang benar sudah menganggap granularitas ini sebagai bagian normal, bukan sisa migrasi terbuka. **Test terkait sudah diupdate:** `test_ac_07_03_group_by_granularitas_18_0` (`asa_analysis/tests/test_sale_report.py`, sebelumnya bernama `test_ac_07_03_group_by_tidak_lagi_memecah_baris`), assertion `len(rows) == 2`.
  3. **Field `sale.order.line.amount_to_invoice` → `asa_amount_to_invoice`** (MF-02, disetujui pemilik modul 2026-08-21) — core 18.0 menambahkan field Monetary BARU dengan nama yang collide (`amount_to_invoice`, dipakai jalur credit-limit partner). Modul di-rename ke namespace `asa_` supaya tidak menimpa field core. **Ini bagian permanen dari baseline** — TIDAK di-revert ke `amount_to_invoice` di migrasi 18→19 kecuali ada alasan kompatibilitas baru yang eksplisit.

---

## Cara Pakai

1. Dokumen ini adalah rekonsiliasi 1:1 dari `doc-dev/migration_17.0_18.0/doc/01_intake/01b_BASELINE_SPEC.md` + `doc-dev/migration_17.0_18.0/doc/FINDINGS.md` (MF-01, MF-02) ke baseline 18.0 — bukan penulisan ulang independen.
2. Dipakai sebagai input `03_spec/03_MIGRATION_SPEC.md` (strategi teknis port ke 19.0) dan `05_acceptance/05a_MIGRATION_ACCEPTANCE_CRITERIA.md` (tiap AC migrasi wajib sebut `BSL-NNN` yang diverifikasi tetap identik pasca migrasi).
3. ID `BSL-NNN` TIDAK diubah/dipakai ulang untuk klaim lain sepanjang project migrasi 18→19 ini.
