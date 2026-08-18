# Dev Testing — advanced_sales_analysis

**Step:** 04 — Developer Testing (backfill)
**Module:** `advanced_sales_analysis`
**Spec ref:** `doc-dev/backfill/spec/01A_FUNCTIONAL_SPEC.md`
**Test plan ref:** `doc-dev/backfill/test/03B_TEST_PLAN.md`
**Last Updated:** 2026-08-18
**Mode eksekusi:** **Mode C** (Claude Code CLI menjalankan container sendiri)

> **Status test sebelum BACKFILL:** modul TIDAK punya `tests/` sama sekali — nol method, jadi tidak
> ada klasifikasi Lengkap/Stub yang perlu dilakukan. Seluruh 36 test di bawah baru ditulis
> BACKFILL di Step 04.

---

## 0. Hasil Eksekusi (bukti gate)

```
2026-08-18 09:21:05 odoo.tests.result:
0 failed, 0 error(s) of 36 tests when loading database 'advanced_sales_analysis_test'
Initiating shutdown
```

| Item | Nilai |
|---|---|
| Environment | `docker-env/` — `odoo:17.0` (build kustom + Chrome untuk Step 07), `postgres:15` |
| Perintah | `odoo -d advanced_sales_analysis_test -u advanced_sales_analysis --test-enable --test-tags=/advanced_sales_analysis --stop-after-init` |
| Total test | 36 |
| Gagal / error | 0 / 0 |
| File test | `advanced_sales_analysis/tests/{common,test_account_move,test_sale_order_line,test_sale_report}.py` |
| Log mentah | `docker-env/logs/odoo.log` (tidak di-commit, lihat `.gitignore`) |

**Run pertama: 1 failed of 36** — kegagalan itu MENEMUKAN bug baru (F-17), bukan bug di test.
Assertion diperbaiki untuk merekam perilaku yang sebenarnya terjadi (bukan perilaku yang
diharapkan), lalu run kedua lulus penuh. Detail di §2c.

### Catatan environment yang perlu diketahui sesi berikutnya

Run pertama **gagal total sebelum Odoo start** dengan
`psycopg2.errors.UndefinedColumn: column "currency_field" does not exist`. Penyebabnya BUKAN modul:
volume Docker `advanced_sales_analysis_backfill_db-data` masih tersisa dari sesi BACKFILL
2026-08-14 yang memakai **Odoo 16.0**, dan nama project Compose-nya sama persis. Odoo 17 mencoba
membaca database yang dibuat Odoo 16. Perbaikannya `docker compose down -v` (bukan `down`).
Ini kandidat pelajaran untuk BACKFILL sendiri — dicatat di
`doc-dev-backfill/records/advanced_sales_analysis/SUMMARY.md`.

---

## 1. Smoke Test

### Cara Eksekusi

**Mode C** — AI menjalankan `docker compose up` sendiri dan membaca `docker-env/logs/odoo.log`.
Tidak ada bagian yang desk-review.

### Checklist

| # | Area/fitur | Happy path / edge case | Cara | Status |
|---|---|---|---|---|
| 1 | Instalasi modul | `-i advanced_sales_analysis` di DB kosong + demo data | Mode C | ✅ Pass — `0 failed, 0 error(s) of 0 tests`, tidak ada traceback |
| 2 | Kolom SQL view | `amount_received`/`amount_to_invoice`/`waiting_for_payment` ada di `sale_report` | Mode C | ✅ Pass — diverifikasi lewat AC-07-01 |
| 3 | Alur SO→invoice→payment | Nilai ketiga metrik terisi benar untuk kasus lunas sederhana | Mode C | ✅ Pass — AC-04-01, AC-05-01, AC-06-02 |
| 4 | Edge: jurnal umum | Membuat `move_type='entry'` setelah modul terinstall | Mode C | ⚠️ Pass dengan catatan — tidak error, tapi `amount_paid` tersimpan NULL (F-02) |
| 5 | Edge: instalasi atas data existing | 24 `account.move` demo di-recompute saat instalasi | Mode C | ⚠️ Pass dengan catatan — tidak error, tapi SEMUA 24 record dapat `amount_paid`/`amount_paid_cn` = NULL (F-02) |

**Peringatan instalasi yang muncul (bukan error, tapi bukti langsung F-13):** Odoo sendiri
mengeluarkan 13 baris `WARNING ... have the same label` untuk field-field modul ini — di
`account.move`, dan (karena delegasi model) ikut merembet ke `account.payment` dan
`account.bank.statement.line`.

---

## 2. Unit & Integration Test Specification

### 2a. `account.move` — field pembantu

**File:** `models/sale_report.py:30-91` · **Test:** `tests/test_account_move.py`

#### TC-F-01 — `amount_paid` / `amount_paid_cn`

| # | Tipe | Condition | Expected (hasil SEKARANG) | Provenance |
|---|---|---|---|---|
| 01 | Unit | `out_invoice` 100 lunas lewat jurnal | `amount_paid == 100.0` | `[DIKONFIRMASI]` (eksekusi) |
| 02 | Unit | `out_refund` 40 lunas | `amount_paid_cn == 40.0` | `[DIKONFIRMASI]` |
| 03 | Unit | `move_type == 'entry'` | Tidak error; kolom DB tersimpan `NULL`, dibaca `0.0` | `[PERLU-KEPUTUSAN]` F-02 |
| 04 | Unit | `out_invoice` `payment_state == 'not_paid'` | Kolom DB tersimpan `NULL` | `[PERLU-KEPUTUSAN]` F-02 |

#### TC-F-02 — komponen uang muka (`amount_dp*`, `amount_refund*`)

| # | Tipe | Condition | Expected (hasil SEKARANG) | Provenance |
|---|---|---|---|---|
| 01 | Unit | 1 baris produk `"Down payment"` +30, belum dibayar | `amount_dp2_nopaid == 30.0`, `amount_dp2 == 0.0` | `[DIKONFIRMASI]` |
| 02 | Unit | Baris `"Down payment"` −30 di faktur lunas | `amount_dp == -30.0`, `amount_dp_nopaid == 0.0` | `[DIKONFIRMASI]` |
| 03 | Unit | DUA baris `"Down payment"` +30 dan +50 | `amount_dp2_nopaid == 50.0` (bukan 80.0) | `[PERLU-KEPUTUSAN]` F-10 |
| 04 | Unit | Faktur DP terbayar sebagian (`partial`) | `amount_dp2_nopaid == 30.0` (100% dianggap belum dibayar) | `[PERLU-KEPUTUSAN]` F-11 |
| 05 | Unit | Produk DP bernama `"Acompte"` | Keenam field tetap `0.0` — tidak dikenali sebagai DP | `[PERLU-KEPUTUSAN]` F-04 |

### 2b. `sale.order.line` — tiga metrik

**File:** `models/sale_report.py:94-246` · **Test:** `tests/test_sale_order_line.py`

#### TC-SOL-01 — `amount_received`

| # | Tipe | Condition | Expected | Provenance |
|---|---|---|---|---|
| 01 | Integration | SO 100 → faktur → lunas | `100.0` | `[DIKONFIRMASI]` |
| 02 | Integration | Difakturkan, belum dibayar | `0.0` | `[DIKONFIRMASI]` |
| 03 | Integration | Dibayar 60 dari 100 (`partial`) | `60.0` | `[DIKONFIRMASI]` |
| 04 | Integration | Dua baris 60 + 40, satu faktur lunas | `60.0` dan `40.0` | `[DIKONFIRMASI]` |
| 05 | Integration | Credit note penuh yang juga lunas | kembali ke `0.0` | `[DIKONFIRMASI]` |
| 06 | Integration | Baris SO produk `"Down payment"` | `amount_dp2 + amount_dp − amount_refund` | `[DIKONFIRMASI]` |
| 07 | Integration | Faktur ber-`amount_untaxed == 0` (diskon 100%) | `0.0`, tanpa `ZeroDivisionError` | `[PERLU-KEPUTUSAN]` F-16 |

#### TC-SOL-02 — `waiting_for_payment`

| # | Tipe | Condition | Expected | Provenance |
|---|---|---|---|---|
| 01 | Integration | Difakturkan penuh, belum dibayar | `100.0` | `[DIKONFIRMASI]` |
| 02 | Integration | Dibayar 60 dari 100 | `40.0` | `[DIKONFIRMASI]` |
| 03 | Integration | Belum difakturkan | `0.0` | `[DIKONFIRMASI]` |
| 04 | Integration | Faktur di-cancel | `0.0` | `[DIKONFIRMASI]` |
| 05 | Integration | Satu baris SO, dua faktur (A lunas, B belum) | `waiting == 100.0`, `received == 100.0` | `[DIKONFIRMASI]` F-09 |

#### TC-SOL-03 — `amount_to_invoice`

| # | Tipe | Condition | Expected | Provenance |
|---|---|---|---|---|
| 01 | Integration | Belum difakturkan | `100.0` | `[DIKONFIRMASI]` |
| 02 | Integration | Sudah lunas | `0.0` | `[DIKONFIRMASI]` |
| 03 | Unit | SO masih draft | `0.0` | `[DIKONFIRMASI]` |
| 04 | Integration | `invoice_policy == 'delivery'`, 10 dipesan / 4 dikirim | `100.0` — qty terkirim DIABAIKAN | `[PERLU-KEPUTUSAN]` **F-17** |
| 05 | Unit | Baca field dalam dua urutan berbeda | Hasil IDENTIK — tidak terbukti order-dependent | `[HASIL-BACA]` F-03 |

### 2c. Edge Cases & Security

| # | Tipe | Kondisi | Expected (hasil SEKARANG) | Provenance |
|---|---|---|---|---|
| 01 | Unit | `amount_untaxed == 0` di faktur yang dipakai perhitungan | Kontribusi 0, tidak ada `ZeroDivisionError` | `[DIKONFIRMASI]` F-16 |
| 02 | Unit | Faktur di-cancel di tengah alur | Baris faktur diabaikan (`state != 'cancel'`) | `[DIKONFIRMASI]` |
| 03 | Unit | Produk DP dinamai bahasa lain | Logika DP mati diam-diam, tanpa error | `[DIKONFIRMASI]` F-04 |
| 04 | Integration | SO mata uang asing (kurs 1:2) | `price_subtotal` laporan = 50, `amount_received` = 100 | `[DIKONFIRMASI]` F-05 |
| 05 | Integration | Dua baris SO produk sama, nilai berbeda | `sale.report` menghasilkan 2 baris, tidak menyatu | `[DIKONFIRMASI]` F-06 |
| 06 | Unit | Baris `display_type == 'line_section'` | Tidak masuk `sale.report` sama sekali (difilter `_where_sale()` core) | `[DIKONFIRMASI]` |

**Security:** tidak ada test bypass ACL — modul tidak mendefinisikan model baru, tidak menambah
route/controller, dan tidak memuat ACL apa pun (F-07). Tidak ada permukaan security baru yang
bisa diuji.

### 2d. Test Matrix Summary

| Area | Unit | Integration | Provenance |
|---|---|---|---|
| `account.move` — `amount_paid`/`amount_paid_cn` | ✓ | | `[DIKONFIRMASI]` |
| `account.move` — komponen DP | ✓ | | `[DIKONFIRMASI]` |
| `sale.order.line` — 3 metrik | ✓ | ✓ | `[DIKONFIRMASI]` |
| `sale.report` — SQL view | | ✓ | `[DIKONFIRMASI]` |
| Tabrakan registry vs `account_payment` | ✓ | | `[DIKONFIRMASI]` |

### 2e. Ringkasan

- **36 test**, semuanya `TransactionCase` (via `TestSaleCommon`), di-tag
  `@tagged('post_install', '-at_install')`.
- Perintah: `odoo -d advanced_sales_analysis_test -u advanced_sales_analysis --test-enable
  --test-tags=/advanced_sales_analysis --stop-after-init`
- Tidak ada `HttpCase` di Step 04 — bagian HTTP/browser ditangani Step 07 (Mode E).

### 2f. Override/Collision Check terhadap Odoo Core

> Diverifikasi lewat grep terhadap SELURUH addon di image `odoo:17.0` (bukan hanya modul di
> `depends`) plus inspeksi definisi field di database setelah instalasi nyata.

| # | Method / field | Model | Didefinisikan juga oleh | Override total core? | Provenance |
|---|---|---|---|---|---|
| 01 | `_select_sale` | `sale.report` | `sale` (core, `sale/report/sale_report.py:89`) | ☐ Tidak — `super()` dipanggil | `[DIKONFIRMASI]` |
| 02 | `_group_by_sale` | `sale.report` | `sale` (core, `:187`) | ☐ Tidak — `super()` dipanggil | `[DIKONFIRMASI]` |
| 03 | **`amount_paid`** | **`account.move`** | **`account_payment` (core, `:20`)** | **☑ YA — definisi core tertimpa total** | `[PERLU-KEPUTUSAN]` **F-01** |
| 04 | **`_compute_amount_paid`** | **`account.move`** | **`account_payment` (core, `:33`)** | **☑ YA — method core tertimpa total** | `[PERLU-KEPUTUSAN]` **F-01** |
| 05 | `_compute_amount_dp` | `account.move` | — (tidak ada di core mana pun) | ☐ Tidak | `[DIKONFIRMASI]` |
| 06 | `_compute_amount_to_invoice` | `sale.order.line` | Ada di `sale.order` dan `pos_sale`/`sale_timesheet` — **model berbeda** | ☐ Tidak | `[DIKONFIRMASI]` |
| 07 | `_compute_waiting_for_payment_research` | `sale.order.line` | — | ☐ Tidak | `[DIKONFIRMASI]` |
| 08 | `_compute_amount_received_research` | `sale.order.line` | — | ☐ Tidak | `[DIKONFIRMASI]` |
| 09 | `amount_to_invoice` (field) | `sale.order.line` | Core punya `untaxed_amount_to_invoice` — **nama berbeda** | ☐ Tidak | `[DIKONFIRMASI]` |

**Bukti F-01 dari database nyata (bukan hanya baca kode):**

```sql
SELECT name, ttype, store FROM ir_model_fields f JOIN ir_model m ON m.id=f.model_id
WHERE m.model='account.move' AND f.name='amount_paid';
--  amount_paid | float | t     <- definisi modul ini (account_payment: monetary, store=f)

SELECT name, state FROM ir_module_module WHERE name='account_payment';
--  account_payment | installed
```

Kolom fisik `amount_paid` juga BENAR-BENAR dibuat di tabel `account_move` (`double precision`) —
efek langsung dari `store=True` modul ini terhadap field core yang aslinya tidak stored.

### 2g. Incoming Email

**N/A** — modul tidak override `message_process()`/`message_route()`, tidak punya `mail.alias`,
tidak depend `fetchmail.server`.

---

## 3. Temuan Baru dari Step 04 (yang TIDAK terlihat dari baca kode)

| ID | Temuan | Cara ditemukan |
|---|---|---|
| **F-17** | `invoice_policy == 'delivery'` diabaikan — `price_subtotal` lokal jadi dead code | Test gagal di run pertama (100.0 ≠ 40.0) |
| F-01 (naik ke `[DIKONFIRMASI]`) | `account_payment` benar-benar terinstall bersama; definisi modul ini yang menang | Query `ir_model_fields` + `ir_module_module` di DB nyata |
| F-02 (naik ke `[DIKONFIRMASI]`) | Tidak melempar error, tapi menulis `NULL` — 24/24 move demo NULL | Query `account_move` setelah instalasi |
| F-13 (naik ke `[DIKONFIRMASI]`) | Odoo sendiri mem-`WARNING` label duplikat saat instalasi, merembet ke 2 model lain | Log instalasi |
| F-03 (turun prioritas) | Tidak terbukti order-dependent di skenario yang diuji | AC-06-05 lulus dengan hasil identik |
| F-09 (turun prioritas) | Tidak terbukti berdampak — invoice yang lolos filter selalu ber-`amount_residual != 0` | AC-05-05 lulus dengan angka benar |
