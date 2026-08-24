# Migration Intake — advanced_sales_analysis

**Step:** 1 — Intake & Scope
**Versi:** 17.0 → 18.0
**Tanggal:** 2026-08-21
**Status:** Draft — menunggu review user

---

## 0. Folder Referensi

- [x] `native-target` (Community, `odoo/odoo` checkout 18.0) — ADA di disk dev. Path: `D:\Kuncoro\doodex\repo\odoo18` (dikonfirmasi dev, branch `18.0` diverifikasi AI lewat `git branch --show-current`).
- [x] `native-source` (Community, checkout 17.0) — ADA. Path: `D:\Kuncoro\doodex\repo\odoo17` (branch `17.0` diverifikasi).
- [ ] `native-target-enterprise` / `native-source-enterprise` — **Tidak relevan.** Dependency map (§2) tidak punya satu pun baris Enterprise — keempat dependency (`base`, `sale`, `account`, `sale_management`) semuanya Native Community.
- [ ] `third-party-source` / `third-party-target` — **Tidak relevan.** Tidak ada dependency OCA/vendor.

### 0a. Konfirmasi Branch/Versi `source-codebase` & `target-codebase`

- [x] `source-codebase` — branch `migration/17.0_source`. Dikonfirmasi: dibuat AI sendiri lewat Mode Git (`git clone -b migration/17.0_source ... advanced_sales_analysis-migration-18-source`), isinya persis `origin/migration/17.0_source` (= `backfill/17.0` + fix F-19 + re-run test bersih). Path: `D:\Kuncoro\doodex\repo\advanced_sales_analysis-migration-18-source`.
- [x] `target-codebase` — branch `migration/18.0_target`. Dikonfirmasi: dibuat AI sendiri lewat Mode Git (`git checkout -b migration/18.0_target origin/migration/17.0_source` di folder utama, upstream tracking dilepas). Path: `D:\Kuncoro\doodex\repo\advanced_sales_analysis-migration-18` (folder ini, root project).
- [x] Dikonfirmasi dua clone fisik terpisah (bukan symlink/alias) — dibuat lewat `git clone` terpisah, bukan branch-switch di satu folder.

**Catatan penamaan branch (koreksi user, 2026-08-21):** nama branch semula ditebak AI (`18.0`, `advanced_sales_analysis-source-migration`) — SALAH, dikoreksi user jadi pola simetris `migration/{{VERSION}}_source` / `migration/{{VERSION}}_target`. Dicatat di sini supaya tidak terulang di project migrasi lain.

---

## Ringkasan untuk Review — Perlu Konfirmasi User

1. **Baseline spec (01b) diadaptasi dari `doc-dev/backfill/spec/01A_FUNCTIONAL_SPEC.md` + `FINDINGS.md`** (hasil proses BACKFILL terpisah sebelumnya, sudah execution-verified lewat 38 test), bukan ditulis dari nol — source branch (`migration/17.0_source`) adalah `backfill/17.0` + fix F-19. Asumsi: dokumen backfill itu masih akurat merepresentasikan behavior 17.0 saat ini. Mohon konfirmasi kalau ada perubahan source SETELAH 2026-08-21 yang belum tercermin di sana.
2. **18 dari 19 finding di `FINDINGS.md` backfill masih TERBUKA** (F-01 s/d F-18 kecuali F-06/F-08/F-19 yang resolved) — semua diperlakukan sebagai **behavior yang harus dipertahankan identik di 18.0** (bug-compatible migration), BUKAN diperbaiki, sesuai prinsip source-of-truth migrasi. Kalau pemilik modul ingin sekalian memperbaiki salah satu finding SAAT migrasi (bukan port identik) — itu keputusan eksplisit yang perlu disebut sekarang, jangan diasumsikan AI.
3. **F-01 (koleksi nama field `amount_paid`/`_compute_amount_paid` dengan `account_payment`)** masih berpotensi relevan di 18.0 — `account_payment/models/account_move.py` masih ada di native-target. Perlu dicek ulang di Step 2 apakah definisi core `account_payment` di 18.0 berubah (bisa mengubah karakter collision-nya).
4. **Modul tidak punya `views`/XML sama sekali** (`'data': []`, satu-satunya entri di-comment) — artinya risiko migrasi 18.0 terkonsentrasi di kompatibilitas Python (ORM API, hook `_select_additional_fields()`, ownership field), BUKAN di deprecation `attrs`/view API (yang menjadi isu besar migrasi 17→18 pada modul lain yang punya views).
5. Tidak ada deadline spesifik dan owner belum ditentukan (dikonfirmasi user, 2026-08-21) — kalau ada tanggal target atau PIC yang perlu ditambahkan nanti, update §6.

---

## 1. Modul & Scope

- Modul yang dimigrasi: `advanced_sales_analysis` (satu modul, tidak multi-module)
- Deskripsi singkat: memperkaya laporan Sales Analysis (`sale.report`) dengan 3 metrik finansial baru (`amount_received`, `waiting_for_payment`, `amount_to_invoice`), ditopang 3 stored-compute di `sale.order.line` dan 8 stored-compute pembantu di `account.move` untuk memecah nilai faktur (dibayar/belum/uang muka/retur).
- Modul-modul saling depend: N/A (single module)

## 2. Dependency Map

| Dependency | Tipe | Versi tersedia di target (18.0)? | Catatan |
|---|---|---|---|
| `base` | Native Community | Ya (`odoo/addons/base`) | — |
| `sale` | Native Community | Ya (`addons/sale`) | Modul inherit `sale.report`, `sale.order.line` dari sini. Hook `_select_additional_fields()` (dipakai fix F-19) masih ada di 18.0 (`addons/sale/report/sale_report.py:175`) — kompatibel. |
| `account` | Native Community | Ya (`addons/account`) | Modul inherit `account.move` dari sini. |
| `sale_management` | Native Community | Ya (`addons/sale_management`) | Terdaftar sebagai dependency langsung tapi tidak ada penggunaan eksplisit yang teridentifikasi di kode (`_inherit`/API) — kemungkinan cuma memastikan `sale.order`/UI Sales Management ikut terinstall. Perlu dicek lagi di Step 2 kalau ada API `sale_management`-spesifik yang dipakai tidak langsung. |

Dependency opsional yang dicek runtime: tidak ditemukan (tidak ada `in self.env` check di kode).

**Catatan Enterprise/OCA:** Tidak ada. Keempatnya Native Community — `native-target-enterprise`/`third-party-*` tidak perlu di-connect.

**Catatan `point_of_sale` (bukan dependency langsung, tapi relevan):** fix F-19 (di source) membuat 3 kolom baru dipindah ke `_select_additional_fields()` — hook yang sama dipakai ulang oleh `_select_pos()` milik modul `point_of_sale` (Community). Satu test di backfill (`test_f19_union_kompatibel_dengan_point_of_sale`) di-skip karena `point_of_sale` tidak terinstall di image `odoo:17.0` yang dipakai testing — bukan karena modul ini depend ke POS, tapi karena keduanya berbagi hook core yang sama. Perlu tetap diperhatikan di Step 2/9 kalau target environment 18.0 testing punya POS terinstall.

## 2b. Struktur & Fitur Modul

| Fitur | Ada di modul? | Lokasi/bukti | Fase step 6 relevan |
|---|---|---|---|
| Controllers (route custom) | Tidak (secara fungsional) | `controllers/controllers.py` cuma 2 baris komentar, tetap di-import (F-12, finding terbuka — dipertahankan apa adanya) | N/A |
| Assets/CSS/JS custom | Tidak | Tidak ada key `assets` di manifest (F-18) | N/A |
| Komponen Owl/JavaScript custom | Tidak | Tidak ada file `.js` di `static/src/` | N/A |
| Field JSON, relasi berantai (>2 level), dynamic model creation | Tidak | Semua field `Float`; satu `search()` dinamis ke `account.move.line` tapi bukan `self.env[var]` | N/A |
| View pakai `attrs=`/`states=`/`domain=`/`context=` dinamis | Tidak | `'data': []` — tidak ada view/XML sama sekali | N/A |

Semua baris "Ada di modul?" = Tidak → Fase D1/D2/E/F/B2/C2 di Step 6 langsung N/A pada Applicability Check, tanpa perlu dikerjakan satu-satu. Risiko migrasi modul ini terkonsentrasi di kompatibilitas API Python murni (ORM `@api.depends`, SQL raw string di `_select_additional_fields()`/`_select_sale()` kalau masih dipakai, `account_payment` field collision).

## 3. Sifat Migrasi

- [x] Port kode saja (belum ada data produksi — instalasi baru di versi target)
- [ ] Upgrade instance (data produksi) — N/A

## 4. Baseline Spec / Characterization Test (gate)

- [x] Modul punya `FUNCTIONAL_SPEC.md` lama — dari project **doc-dev-backfill** terpisah (bukan migration-tool), lokasi: `source-codebase/doc-dev/backfill/spec/01A_FUNCTIONAL_SPEC.md` (+ `doc-dev/backfill/FINDINGS.md`, `doc-dev/backfill/spec/01B_ACCEPTANCE_CRITERIA.md`, `doc-dev/backfill/test/04A_DEV_TESTING.md`, `doc-dev/backfill/test/07_QA_TESTING.md`).
  - Dokumen ini BUKAN spec requirement asli (module tidak punya spec tertulis dari awal) — dia sendiri hasil rekonstruksi retroaktif dari kode + test eksekusi nyata (38 test, `0 failed 0 error`). Statusnya secara efektif setara characterization test yang sudah divalidasi eksekusi, bukan cuma baca-kode statis.
  - Proses pengisian `01b_BASELINE_SPEC.md`: seluruh klaim `BR-NNN` di `01A_FUNCTIONAL_SPEC.md` dan `F-NNN` di `FINDINGS.md` di-cross-check ulang terhadap kode `source-codebase` saat ini (identik — source branch tidak berubah sejak backfill ulang 2026-08-21) → disalin/dipetakan ke ID `BSL-NNN` dengan tag `[MATCH]` (ref ke `BR-NNN`/`F-NNN` asli), karena cocok 1:1.
- [x] `01b_BASELINE_SPEC.md` sudah diisi — lihat `01_intake/01b_BASELINE_SPEC.md`.

### 4a. Dokumen Pelengkap Lain

- [x] Ditanyakan eksplisit ke dev (2026-08-21): **Dikonfirmasi tidak ada** dokumen pelengkap lain (manual guide, PRD, requirement klien, catatan vendor) di luar `doc-dev/backfill/` yang sudah dibaca.

## 4b. Source Masih Aktif Dikembangkan?

- [x] Tidak — source module dibekukan selama migrasi berjalan (dikonfirmasi dev, 2026-08-21). `SYNC_POLICY.md` tidak diperlukan.

## 5. Scope Boundary

- **Yang harus tetap identik pasca migrasi:** seluruh business rule BR-01 s/d BR-08 (`01A_FUNCTIONAL_SPEC.md`), termasuk 15 finding yang masih terbuka (F-01, F-02, F-03, F-04, F-05, F-07, F-09, F-10, F-11, F-12, F-13, F-14, F-15, F-16, F-17) — ini bug/quirk yang SENGAJA dipertahankan, bukan diperbaiki saat migrasi. Tiga finding yang sudah resolved di source (F-06, F-08, F-19 — semuanya terkait pemindahan ke `_select_additional_fields()`) ikut jadi bagian baseline yang diport (bukan "bug lama" yang perlu direstore).
- **Yang sengaja diubah/di-drop selama migrasi:**
  - **Granularitas baris `sale.report`/Sales Analysis (MF-01, disetujui 2026-08-21).** Core Odoo 18.0 menambah kolom `l.price_unit`/`l.invoice_status`/`l.is_downpayment` ke `_group_by_sale()` (tidak ada di 17.0) — modul ini tidak override method itu, jadi laporan 18.0 otomatis lebih granular (SO dengan baris produk sama tapi `price_unit` berbeda TIDAK lagi menyatu jadi satu baris laporan, beda dari 17.0). Pemilik modul memutuskan menerima behavior baru ini apa adanya (Opsi 1 di `FINDINGS.md` MF-01) — TIDAK mencoba memaksa granularitas lama lewat override `_group_by_sale()` manual (yang berisiko menghidupkan kembali pola bug F-19). Lihat `FINDINGS.md` MF-01 untuk detail lengkap.

## 6. Constraint

- Deadline: Tidak ada deadline spesifik (dikonfirmasi dev, 2026-08-21).
- Owner tiap step: Belum ditentukan — akan diisi kalau relevan.
