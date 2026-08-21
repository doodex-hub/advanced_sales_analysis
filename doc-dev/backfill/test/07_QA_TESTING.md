# QA Testing — advanced_sales_analysis

**Step:** 07 — QA Testing (backfill, TANPA UAT — BACKFILL berhenti di sini)
**Ref:** `spec/01A_FUNCTIONAL_SPEC.md`, `spec/01B_ACCEPTANCE_CRITERIA.md`, `test/03B_TEST_PLAN.md`
**Tanggal:** 2026-08-18 (backfill awal) · **Diperbarui:** 2026-08-21 (backfill ulang, fix F-19)
**Environment:** Claude Code CLI · Mode C (eksekusi container) + Mode E (Chrome headless)

> File ini sekaligus skenario, tracker, dan laporan. Tidak ada `07B_QA_AI_BROWSER.md` —
> lihat §2 untuk alasannya.

---

## 1. Area / AC yang Harus Dicakup

- [x] Instalasi modul di database bersih dengan demo data (AC-01-01)
- [x] Ketiga measure baru muncul & bisa dipakai di pivot Sales Analysis (AC-01-02)
- [x] Dampak tabrakan `amount_paid` dengan `account_payment` (AC-01-03)
- [x] Alur end-to-end SO → faktur → pembayaran, angka ketiga metrik (AC-04/05/06)
- [x] Perilaku modul terhadap dokumen akuntansi di luar penjualan (AC-02-03)
- [x] Skenario mata uang asing (AC-07-04)
- [x] Granularitas baris laporan — **F-06 RESOLVED** (AC-07-03: kini 1 baris, bukan 2)
- [x] Skenario uang muka, termasuk database non-Inggris (AC-03-*)
- [x] **Skenario wajib "hanya satu dialog/wizard disentuh"** — dievaluasi, hasilnya **N/A dengan
      alasan** (lihat S-08). Tidak dilewat diam-diam.

---

## 2. Metode Eksekusi — kenapa `browser_js`, bukan `start_tour`

`PLAYBOOK.md` §Mode E menetapkan **Tour headless** sebagai default Step 07 di CLI. Di modul ini
jalur itu **tidak bisa dipakai apa adanya**, dan alasannya penting untuk dicatat:

`start_tour()` mensyaratkan file Tour JS terdaftar di bundle `web.assets_tests`. Pendaftaran itu
dilakukan lewat key `assets` di `__manifest__.py`. **Modul ini tidak punya key `assets` sama
sekali** — jadi memakai Tour berarti menambah key baru ke manifest, yaitu mengubah file modul di
luar `tests/`. Itu di luar mandat BACKFILL ("hanya boleh menambah file test").

Jalur yang dipakai: **`HttpCase.browser_js()`** — kode JS dikirim sebagai string dari Python,
dijalankan di Chrome headless yang sama yang dipakai Tour, terhadap webclient OWL yang sama.
Lapisan bukti yang didapat identik (JS asli jalan, klik asli, DOM asli), tanpa menyentuh satu pun
file di luar `tests/`. Prasyarat image-nya sama persis dengan Mode E (`docker-env/Dockerfile`
dengan Google Chrome + `websocket-client`), dan bukti Chrome benar-benar menyala ada di log:

```
Chrome pid: 16
Browser version: Chrome/150.0.7871.186
```

Ini dicatat sebagai F-18 di `FINDINGS.md` (untuk pemilik modul) dan sebagai kandidat pelajaran
untuk BACKFILL sendiri di `doc-dev-backfill/records/advanced_sales_analysis/SUMMARY.md`.

**`07B_QA_AI_BROWSER.md` tidak dibuat** — file itu untuk verifikasi lewat Claude in Chrome. Di sesi
ini verifikasi browser sudah dilakukan lewat Chrome headless nyata (lebih kuat: reproducible, ikut
ter-commit sebagai test), jadi file terpisah itu tidak punya isi yang berbeda untuk ditulis.

---

## 3. Skenario

### S-01: Instalasi modul di database bersih
**Precondition:** Postgres kosong, `odoo:17.0`, demo data aktif
**Mode eksekusi:** Mode C (docker, nyata)
**Steps:**
1. `docker compose up` dengan `-i advanced_sales_analysis`
2. Baca `docker-env/logs/odoo.log` sampai `Initiating shutdown`
**Expected:** modul terinstall tanpa traceback
**Actual:** `0 failed, 0 error(s) of 0 tests`, `54 modules loaded`, tidak ada traceback. Muncul 13
baris `WARNING ... have the same label` (bukti F-13). `account_payment` ikut terinstall otomatis.
**Status:** ☑ Pass
**Provenance:** `[DIKONFIRMASI]`

### S-02: Alur end-to-end SO → faktur → pembayaran
**Precondition:** modul terinstall, produk servis 100 tanpa pajak
**Mode eksekusi:** Mode C (36 `TransactionCase`)
**Steps:**
1. Buat SO 1 × 100, konfirmasi
2. Buat faktur dari SO, post
3. Daftarkan pembayaran (penuh / sebagian 60)
4. Baca `amount_received`, `waiting_for_payment`, `amount_to_invoice` di baris SO
5. `flush_all()` lalu baca `sale.report` untuk order yang sama
**Expected:** belum dibayar → waiting 100 / received 0; dibayar 60 → waiting 40 / received 60;
lunas → received 100 / to_invoice 0; nilai `sale.report` sama dengan nilai baris SO
**Actual:** semua sesuai. Kesesuaian `sale.report` ↔ baris SO diverifikasi di AC-07-01.
**Status:** ☑ Pass
**Provenance:** `[DIKONFIRMASI]`

### S-03: Measure baru tampil dan bisa dipakai di pivot Sales Analysis
**Precondition:** modul terinstall, ada minimal satu SO terkonfirmasi
**Mode eksekusi:** **Mode E** — Chrome headless via `HttpCase.browser_js`
**Steps:**
1. Login `admin`, buka action `sale.action_order_report_all`
2. Klik switcher `button.o_switch_view.o_pivot` (action default membuka **Graph**, bukan Pivot)
3. Klik tombol **Measures** di `.o_pivot_buttons`
4. Baca isi dropdown `.o-dropdown--menu`
5. Pilih **Amount Received**, tunggu render, cek `thead` tabel pivot
**Expected:** ketiga measure baru ada di dropdown; setelah dipilih, kolomnya muncul di header pivot
**Actual:** ketiga measure (`Amount Received`, `Waiting for Payment`, `Amount To Invoice`) ada dan
bisa dipilih; kolom `Amount Received` muncul di `thead`. `console.log("test successful")` tercapai.
**Status:** ☑ Pass
**Provenance:** `[DIKONFIRMASI]`
**Catatan selector (2 percobaan):** percobaan pertama gagal — tombol Measures dicari di
`.o_control_panel`, padahal di Odoo 17 tombol itu dirender oleh Renderer ke `.o_pivot_buttons`
(dikonfirmasi dengan membaca `web/static/src/views/pivot/pivot_controller.xml` +
`web/static/src/views/view.xml`, bukan tebakan). Item dropdown-nya `.o_menu_item`, bukan
`.dropdown-item` polos.

### S-04: Membuat dokumen akuntansi di luar penjualan setelah modul terinstall
**Precondition:** modul terinstall
**Mode eksekusi:** Mode C
**Steps:**
1. Buat `account.move` `move_type='entry'` (jurnal umum) dengan 2 baris seimbang
2. Flush, invalidate, baca `amount_paid`/`amount_paid_cn`
3. Query kolom fisiknya langsung lewat SQL
**Expected (dugaan Step 01):** error "Compute method failed to assign"
**Actual:** **tidak ada error.** Kolom tersimpan `NULL`, dibaca `0.0` dari Python. Berlaku juga
untuk 24 dari 24 `account.move` demo. Dugaan Step 01 SALAH — F-02 dikoreksi.
**Status:** ☑ Pass (perilaku terekam, bukan tanpa masalah — lihat F-02)
**Provenance:** `[DIKONFIRMASI]`

### S-05: Order dalam mata uang asing
**Precondition:** kurs EUR 1:2 terhadap mata uang perusahaan
**Mode eksekusi:** Mode C
**Steps:**
1. Buat pricelist EUR, SO 1 × 100 EUR, konfirmasi, faktur, bayar lunas
2. Baca `sale.report` untuk order itu
**Expected:** kolom core dikonversi, kolom baru tidak
**Actual:** `price_subtotal` laporan = **50**, `amount_received` laporan = **100**. Terkonfirmasi
F-05: dua kolom di baris yang sama memakai satuan berbeda.
**Status:** ☑ Pass (perilaku terekam — lihat F-05)
**Provenance:** `[DIKONFIRMASI]`

### S-06: Dua baris SO produk sama, nilai berbeda
**Precondition:** SO dengan dua baris produk identik, harga 60 dan 40
**Mode eksekusi:** Mode C
**Steps:**
1. Buat SO, konfirmasi
2. Hitung jumlah baris `sale.report` untuk order itu
**Expected (backfill awal 2026-08-18):** 2 baris — F-06 terkonfirmasi, granularitas berubah.
**Expected (backfill ulang 2026-08-21):** **1 baris** — F-06 RESOLVED. `_select_additional_fields()`
tidak menyentuh GROUP BY, sehingga granularitas laporan kembali identik dengan core.
**Actual (2026-08-21):** **1 baris** — diverifikasi lewat `test_ac_07_03_group_by_tidak_lagi_memecah_baris`.
**Status:** ☑ Pass — **F-06 RESOLVED**
**Provenance:** `[DIKONFIRMASI]`

### S-07: Skema uang muka, termasuk database non-Inggris
**Precondition:** produk bernama `"Down payment"` dan produk bernama `"Acompte"`
**Mode eksekusi:** Mode C
**Steps:**
1. Faktur dengan baris DP positif (belum dibayar) → cek `amount_dp2_nopaid`
2. Faktur dengan baris DP negatif (lunas) → cek `amount_dp`
3. Faktur dengan DUA baris DP positif (30 dan 50) → cek `amount_dp2_nopaid`
4. Faktur DP terbayar sebagian → cek `amount_dp2` vs `amount_dp2_nopaid`
5. Faktur dengan produk `"Acompte"` → cek keenam field DP
**Expected:** jalur DP aktif hanya untuk nama persis `"Down payment"`
**Actual:** (1) 30 ✓ (2) −30 ✓ (3) **50, bukan 80** → F-10 (4) semua ke `nopaid` → F-11
(5) keenam field tetap `0.0` → F-04 terkonfirmasi, logika DP mati total di DB non-Inggris.
**Status:** ☑ Pass (perilaku terekam — lihat F-04, F-10, F-11)
**Provenance:** `[DIKONFIRMASI]`

### S-08: Skenario wajib "hanya satu dialog/wizard disentuh"
**Precondition:** —
**Mode eksekusi:** Evaluasi struktural (bukan eksekusi)
**Steps:**
1. Cek apakah modul mendefinisikan view/wizard/dialog apa pun
2. Cek apakah modul `_inherit` wizard core mana pun
3. Cek apakah ada aksi user yang bisa memicu >1 dialog dari modul ini
**Expected:** teridentifikasi ada/tidaknya kandidat skenario
**Actual:** **N/A dengan alasan.** Modul tidak punya `views/`, tidak punya `wizard/`, `'data': []`,
tidak ada JS/asset, dan tidak meng-`_inherit` wizard mana pun. Tidak ada satu pun dialog yang
berasal dari modul ini, jadi tidak ada kombinasi "dua dialog dari satu aksi" yang bisa dibentuk.
Wizard uang muka (`sale.advance.payment.inv`) yang muncul di alur DP adalah wizard core murni yang
tidak disentuh modul ini.
**Status:** ☑ N/A (dievaluasi eksplisit, bukan dilewat)
**Provenance:** `[DIKONFIRMASI]`

### S-10: Kompatibilitas UNION `sale.report` dengan `point_of_sale` (F-19)
**Precondition:** modul `advanced_sales_analysis` terinstall; environment `fsdemo17`/
`demo17_odoo_store` (production, bukan `docker-env/` isolasi backfill)
**Mode eksekusi:** manual UI (browser nyata) + verifikasi silang lewat Mode C (`test_f19_union_kompatibel_dengan_point_of_sale`)
**Ditemukan:** post-backfill, production `demo17.doodex.net`, 20 Agustus 2026. Dikonfirmasi ulang
21 Agustus 2026 di `fsdemo17`.
**Steps:**
1. Modul `advanced_sales_analysis` terinstall, `point_of_sale` BELUM terinstall — buka Sales →
   Reporting → Sales (List/Pivot view) → **tidak error**.
2. Install `pos_margin_threshold` (depends `point_of_sale`) → buka lagi Sales → Reporting → Sales →
   **`psycopg2.errors.SyntaxError: each UNION query must have the same number of columns`**.
3. Uninstall `point_of_sale` → buka lagi laporan → error **hilang**. Ini konfirmasi langsung akar
   masalah: `point_of_sale` (lewat `pos_sale/report/sale_report.py`) menambah cabang UNION kedua ke
   `sale.report._query()`, dan 3 kolom tambahan modul ini (via override manual `_select_sale()`)
   tidak ikut ditambahkan ke cabang itu.
4. Terapkan fix: ganti override `_select_sale()`/`_group_by_sale()` dengan `_select_additional_fields()`.
5. Install ulang `point_of_sale` → buka lagi laporan Sales Analysis.
**Expected:** laporan terbuka normal di KEDUA kondisi — dengan dan tanpa `point_of_sale` terinstall.
**Actual:** langkah 1-4 dikonfirmasi persis seperti Expected di atas lewat tes manual UI langsung
(screenshot dari user, 21 Agustus 2026). Langkah 5 (retest setelah fix, dengan POS terinstall)
**belum dikonfirmasi hasil akhirnya** pada saat dokumen ini ditulis — command server sudah
diberikan ke user (`docker exec ... odoo -u advanced_sales_analysis ...` lalu restart), menunggu
laporan hasil buka Sales Analysis pasca-fix.
**Status:** ☑ **Pass** — fix `_select_additional_fields()` terverifikasi dari dua sisi:
- Tes manual UI di `fsdemo17` (screenshot user, 2026-08-21): laporan Sales Analysis terbuka normal
  dengan `point_of_sale` terinstall.
- Regression guard `test_f19_union_kompatibel_dengan_point_of_sale` **di-skip** di environment
  `odoo:17.0` standar (POS tidak terinstall — perilaku yang diharapkan; menginstall modul di dalam
  `TransactionCase` dilarang Odoo 17). Guard aktif jika test dijalankan di database dengan POS.
**Provenance:** `[DIKONFIRMASI]` — root cause (langkah 1-3) + fix final (langkah 5) keduanya
sudah terkonfirmasi lewat tes manual UI.

### S-09: Dampak nyata tabrakan `amount_paid` terhadap fitur `account_payment`
**Precondition:** `account_payment` terinstall (kondisi default)
**Mode eksekusi:** Mode C (sebagian) + **tidak dieksekusi** (sebagian)
**Steps:**
1. Verifikasi definisi field mana yang menang di registry ✓
2. Verifikasi semantiknya ikut tergantikan ✓
3. Verifikasi dampaknya ke portal pembayaran pelanggan ✗
**Expected:** definisi modul ini menang; portal `account_payment` menampilkan angka dengan arti
yang berubah
**Actual:** langkah 1-2 **terbukti** — `ir_model_fields` menunjukkan `float`/`store=t` (definisi
modul ini), dan invoice tanpa `payment.transaction` melaporkan `amount_paid == 100.0` (semantik
modul ini), bukan `0.0` (semantik `account_payment`). Langkah 3 **tidak dieksekusi** — lihat
keterbatasan di §4.
**Status:** ☑ Pass sebagian
**Provenance:** `[DIKONFIRMASI]` untuk langkah 1-2, `[PERLU-KEPUTUSAN]` untuk dampak akhirnya (F-01)

---

## 4. Status Sub-file & Rekap Eksekusi

| File | Isi | Status | Dieksekusi? | Mode |
|---|---|---|---|---|
| §3 di file ini | Skenario S-01 … S-09 | ✅ Selesai | Ya (8 dari 9 penuh, S-09 sebagian) | Mode C + Mode E |
| `07B_QA_AI_BROWSER.md` | Verifikasi Claude in Chrome | N/A | Tidak | — (lihat §2) |

**Bukti eksekusi gabungan Step 04 + Step 07 (backfill ulang 2026-08-21):**

```
2026-08-21 odoo.tests.result:
0 failed, 0 error(s) of 38 tests when loading database 'advanced_sales_analysis_test'
```

38 test = 37 Mode C (termasuk 1 regression guard F-19 yang **di-skip** — POS tidak terinstall di
`odoo:17.0`) + 1 browser HttpCase (Step 07). Total dihitung Odoo termasuk yang di-skip.

**Referensi run awal 2026-08-18:** `0 failed, 0 error(s) of 37 tests`
(36 Step 04 + 1 Step 07).

### Keterbatasan eksekusi — WAJIB dibaca

1. **Dampak akhir F-01 ke portal pembayaran tidak diverifikasi end-to-end.** Membuktikannya butuh
   `payment_provider` yang aktif dan `payment.transaction` sungguhan (biasanya butuh provider
   eksternal/demo provider yang dikonfigurasi). Yang SUDAH terbukti adalah akar masalahnya:
   definisi dan semantik field core benar-benar tergantikan. Dampak turunannya ke UI portal
   disimpulkan dari membaca `account_payment/models/account_move.py` (`_has_to_be_paid()` dan
   template portal membaca `amount_paid`), bukan dari eksekusi — dan ditandai begitu, tidak
   disamarkan sebagai sudah dites.
2. **Performa F-15 tidak diukur.** Kekhawatiran `search()` di dalam loop bersarang hanya terasa di
   database berukuran produksi. Database test (demo data) terlalu kecil untuk memberi angka yang
   berarti. Tidak ada klaim performa yang dibuat di dokumen ini.
3. **Tidak ada verifikasi UI untuk F-13 di `account.payment` / `account.bank.statement.line`.**
   Bukti bahwa field modul merembet ke dua model itu berasal dari WARNING instalasi Odoo, bukan
   dari membuka form-nya di browser.

---

## 5. Rekap Findings

| Tag | Jumlah | Catatan |
|---|---|---|
| `[PERLU-KEPUTUSAN]` | 19 (F-01 … F-19) | |
| `[DIKONFIRMASI]` lewat eksekusi | 11 + F-19 = **12** | F-19 ditambahkan di Step 07 backfill ulang |
| ✅ RESOLVED (2026-08-21) | 3 (F-06, F-08, F-19) | Efek dari fix F-19 |
| Masih `[HASIL-BACA]` (belum diuji langsung) | 7 (F-03, F-07, F-09, F-12, F-14, F-15) | F-08 dihapus (resolved) |

**Perubahan prioritas berdasarkan bukti eksekusi (bukan pembacaan ulang kode):**

| ID | Step 01 | Setelah eksekusi | Alasan |
|---|---|---|---|
| F-01 | Tinggi (dugaan) | Tinggi (terbukti) | Query DB membuktikan definisi core tertimpa |
| F-02 | Tinggi (dugaan error) | Tinggi (bukan error, tapi NULL) | Prediksi error tidak terbukti — dikoreksi |
| F-03 | Tinggi | **Rendah** | Order-dependency tidak teramati |
| F-09 | Tinggi | **Rendah** | Guard tidak pernah aktif secara struktural |
| F-17 | — | **Tinggi (baru)** | Ditemukan dari kegagalan test, bukan dari baca kode |

**Verdict:** Backfill dokumentasi selesai sampai Step 07 (QA Testing) — **versi backfill ulang
2026-08-21** dengan fix F-19 terintegrasi. **Tidak ada sign-off** — ini bukan release gate.
Keputusan atas **16 item** `[PERLU-KEPUTUSAN]` yang masih terbuka di `FINDINGS.md` ada di tangan
pemilik modul (3 dari 19 total sudah RESOLVED: F-06, F-08, F-19).

---

## 6. Bug / Perlu Perbaikan (konsolidasi)

| Ditemukan di | Scenario | Ringkasan masalah | Status perbaikan |
|---|---|---|---|
| §3 | S-01, S-09 | F-01 — `amount_paid`/`_compute_amount_paid` menimpa definisi core `account_payment` | ☐ Belum |
| §3 | S-04 | F-02 — `_compute_amount_paid` tidak assign di mayoritas cabang, kolom tersimpan `NULL` | ☐ Belum |
| Step 04 | AC-06-04 | F-17 — `invoice_policy='delivery'` diabaikan, `price_subtotal` lokal dead code | ☐ Belum |
| §3 (baru, post-backfill) | S-10 | F-19 — UNION column mismatch dengan `point_of_sale`, laporan Sales Analysis error total | ✅ RESOLVED 2026-08-21 — `_select_additional_fields()` |
| §3 | S-07 | F-04 — deteksi uang muka lewat nama produk hardcoded | ☐ Belum |
| §3 | S-05 | F-05 — kolom baru tidak dikonversi mata uang | ☐ Belum |
| §3 | S-06 | F-06 — GROUP BY tambahan mengubah granularitas laporan core | ✅ RESOLVED 2026-08-21 — efek samping fix F-19 |
| §3 | S-07 | F-10, F-11 — DP ganda hanya baris terakhir; `partial` tidak konsisten | ☐ Belum |
| §3 | S-01 | F-13 — label field duplikat, merembet ke 2 model lain | ☐ Belum |
| §2 | — | F-18 — modul tidak punya bundle `assets`, tidak bisa menampung Tour test | ☐ Belum |

Sisanya (F-03, F-07, F-08, F-09, F-12, F-14, F-15, F-16) prioritas Rendah/Sedang — detail lengkap
di `FINDINGS.md`.

---

## 7. Slot Metode Masa Depan

Belum ada. `07C_QA_PLAYWRIGHT.md` tidak dibuat — belum ada kebutuhan E2E di luar apa yang sudah
dicakup `browser_js`.
