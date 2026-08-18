# Test Plan — advanced_sales_analysis

**Module:** `advanced_sales_analysis`
**Ref:** `doc-dev/backfill/spec/01B_ACCEPTANCE_CRITERIA.md`
**Taxonomy:** vocab test intrinsik Odoo (`TransactionCase` / `HttpCase` / `Tour`) —
`cicd/test_design/odoo-testing-taxonomy.md` tidak di-connect di sesi ini, istilah belum disamakan
ke taxonomy resmi Doodex (catatan konsistensi kosmetik, bukan gap; lihat `PLAYBOOK.md` §0)
**Dibuat oleh:** BACKFILL (Step 03B, backfill)
**Last Updated:** 2026-08-18

> Peta AC → tipe test. BACKFILL berhenti di Step 07 — tidak ada UAT/Step 08/09.
>
> **Definisi yang dipakai di sini:**
> - **Unit** = `TransactionCase` yang membuat record satu model secara langsung dan memeriksa satu
>   compute/field, tanpa alur lintas dokumen.
> - **Integration** = `TransactionCase` yang menjalankan alur nyata lintas model
>   (SO → confirm → invoice → payment → `sale.report`).
> - **Smoke** = modul terinstall bersih dan laporan bisa dibuka tanpa error.

---

## Step 04 — Developer Testing (backfill)

**Output:** `04A_DEV_TESTING.md` + `advanced_sales_analysis/tests/*.py`.
`04B_API_TEST.md` **tidak dibuat** — lihat ringkasan API di bawah.

| AC | Deskripsi singkat | Unit | Integration | API |
|---|---|---|---|---|
| AC-01-01 | Modul terinstall, 3 kolom ada di SQL view `sale_report` | ✓ | | |
| AC-01-02 | 3 measure baru muncul di dropdown Measures | | | *(Step 07)* |
| AC-01-03 | Tabrakan `amount_paid` vs `account_payment` (inspeksi registry/MRO) | ✓ | | |
| AC-02-01 | `amount_paid` = total − residual untuk `out_invoice` lunas | ✓ | | |
| AC-02-02 | `amount_paid_cn` untuk `out_refund` lunas | ✓ | | |
| AC-02-03 | `move_type` `entry`/`in_invoice` → compute tidak assign | ✓ | | |
| AC-02-04 | `out_invoice` `not_paid` → compute tidak assign | ✓ | | |
| AC-03-01 | Baris DP positif belum dibayar → `amount_dp2_nopaid` | ✓ | | |
| AC-03-02 | Baris DP negatif sudah dibayar → `amount_dp` | ✓ | | |
| AC-03-03 | Dua baris DP sekategori → hanya yang terakhir menang | ✓ | | |
| AC-03-04 | DP `payment_state == 'partial'` → dianggap belum dibayar | ✓ | | |
| AC-03-05 | Produk DP bernama non-Inggris → logika DP mati diam-diam | ✓ | | |
| AC-04-01 | `amount_received` = 100 untuk SO lunas sederhana | | ✓ | |
| AC-04-02 | `amount_received` = 0 kalau faktur belum dibayar | | ✓ | |
| AC-04-03 | Pembayaran sebagian (60 dari 100) | | ✓ | |
| AC-04-04 | Proporsi dua baris berbeda produk (60/40) | | ✓ | |
| AC-04-05 | Credit note terbayar mengurangi `amount_received` | | ✓ | |
| AC-04-06 | Baris SO produk DP → jalur `amount_dp*`, bukan proporsional | | ✓ | |
| AC-04-07 | Faktur `amount_untaxed == 0` → kontribusi 0 | | ✓ | |
| AC-05-01 | `waiting_for_payment` = 100 untuk faktur belum dibayar | | ✓ | |
| AC-05-02 | Pembayaran sebagian → sisa 40 | | ✓ | |
| AC-05-03 | Belum difakturkan → 0 | | ✓ | |
| AC-05-04 | Faktur di-cancel diabaikan | | ✓ | |
| AC-05-05 | Multi-faktur → `amount_residual` bocor dari iterasi terakhir | | ✓ | |
| AC-06-01 | `amount_to_invoice` = 100 sebelum difakturkan | | ✓ | |
| AC-06-02 | `amount_to_invoice` = 0 setelah lunas | | ✓ | |
| AC-06-03 | SO draft → 0 | ✓ | | |
| AC-06-04 | `invoice_policy == 'delivery'` pakai `qty_delivered` | | ✓ | |
| AC-06-05 | Dependency melingkar antar 3 compute | ✓ | | |
| AC-07-01 | `sale.report.amount_received` cocok dengan baris SO | | ✓ | |
| AC-07-02 | Baris tanpa `product_id` → 0 | | ✓ | |
| AC-07-03 | GROUP BY tambahan memecah baris laporan | | ✓ | |
| AC-07-04 | Kolom baru tidak dikonversi mata uang | | ✓ | |

**Ringkasan:** 33 AC item → **12 Unit**, **20 Integration**, **1 khusus Step 07** (AC-01-02).
**API:** N/A — modul tidak meng-expose endpoint apa pun (`controllers/controllers.py` kosong,
lihat F-12). `04B_API_TEST.md` TIDAK dibuat.
**Email:** N/A — modul tidak menyentuh email outgoing maupun incoming sama sekali (tidak ada
`mail.thread`, `message_process`, `mail.alias`, `fetchmail`, maupun composer). Service
`mailpit`/`greenmail` **tidak** ditambahkan ke `docker-env/`.

### Catatan teknis wajib untuk penulisan test

1. **`self.env.flush_all()` sebelum query `sale.report`** — `sale.report` adalah SQL view
   (`_auto=False`) yang membaca `sale_order_line` langsung, mem-bypass cache ORM. Tanpa flush,
   nilai stored-compute yang baru ditulis di transaksi yang sama belum ada di database dan query
   mengembalikan nilai lama/0. Terbukti jadi penyebab kegagalan test palsu di sesi sebelumnya —
   lihat `doc-dev-backfill/records/advanced_sales_analysis/SUMMARY.md` CAND-03.
2. **Urutan pembacaan field** untuk AC-06-05 — karena ketiga compute saling depends (F-03), test
   harus membaca dalam DUA urutan berbeda (A: `amount_received` dulu; B: `amount_to_invoice` dulu)
   dan membandingkan hasilnya. Kalau berbeda, itu bukti order-dependency.
3. **AC-02-03 / AC-02-04 kemungkinan besar berupa error, bukan nilai** — test ditulis untuk
   MEREKAM perilaku yang terjadi (`assertRaises` atau nilai apa adanya), bukan memaksa perilaku
   yang "seharusnya". Kalau ternyata tidak error, itu justru informasi penting (berarti
   `account_payment` yang menang di MRO — lihat F-01).
4. **Produk uang muka** — pakai produk yang dirujuk `sale.default_deposit_product_id` dan/atau
   produk bernama persis `"Down payment"` supaya cabang DP benar-benar aktif (F-04).
5. **Batas workaround test-only** — kalau environment gagal karena masalah DI KODE MODUL, maksimal
   SATU workaround test-only; kalau gagal, `skipTest()` eksplisit + catat di `FINDINGS.md`.

---

## Step 07 — QA Testing (AI-interaktif + Smoke, TANPA UAT)

**Output:** `07_QA_TESTING.md` (skenario + tracker + laporan, satu file).
`07B_QA_AI_BROWSER.md` **kondisional** — hanya kalau Claude in Chrome dipakai; default CLI adalah
**Mode E (Tour headless)** yang hasilnya dilaporkan di `07_QA_TESTING.md` §4/§5.

| AC | Deskripsi singkat | AI-interaktif (07 §3) | Tour headless / AI-Browser |
|---|---|---|---|
| AC-01-01 | Modul terinstall bersih, tidak ada traceback di log | ✓ | |
| AC-01-02 | 3 measure baru muncul & bisa dipilih di pivot Sales Analysis | ✓ | ✓ |
| AC-01-03 | Dampak tabrakan `amount_paid` terlihat di UI portal/invoice | ✓ | |
| AC-02-03 | Membuat jurnal umum dari UI Accounting | ✓ | ✓ |
| AC-04-01 | Alur end-to-end SO → invoice → payment, angka di pivot benar | ✓ | ✓ |
| AC-05-01 | Angka Waiting for Payment di pivot untuk faktur belum dibayar | ✓ | ✓ |
| AC-07-03 | Jumlah baris pivot dibanding tanpa modul | ✓ | |
| AC-07-04 | Angka multi-mata-uang di pivot | ✓ | |

**Skenario wajib "hanya satu dialog/wizard disentuh":** **N/A dengan alasan** — modul tidak
mendefinisikan view, wizard, maupun dialog apa pun (`'data': []`, tidak ada `wizard/`). Tidak ada
satu aksi user yang bisa memicu lebih dari satu dialog dari modul ini. Wizard uang muka
(`sale.advance.payment.inv`) yang dipakai di skenario Step 07 adalah wizard core murni, tidak
disentuh/di-`_inherit` modul ini. Cek ini tetap dijalankan sebagai pertanyaan eksplisit, dan
hasilnya dicatat di sini — bukan dilewat diam-diam.

**Catatan Tour (Mode E) untuk Odoo 17.0:** pakai API modern
`registry.category("web_tour.tours").add(...)` — API legacy `odoo.define` + `tour.register` adalah
untuk Odoo ≤16 (lihat `records/advanced_sales_analysis/SUMMARY.md` CAND-01; sesi sebelumnya salah
memakai API modern di database 16.0). Verifikasi cepat sebelum menulis Tour:
`docker run --rm odoo:17.0 grep -rl 'registry.category("web_tour.tours")' <addons> | head -1` —
kalau ada hasil, API modern benar.
Dua gotcha selector lain yang sudah terbukti: dropdown OWL terbuka pakai `.o-dropdown--menu`
(bukan `.dropdown-menu.show`, CAND-02), dan action Sales Analysis default membuka **Graph view**
sehingga Tour harus klik `button.o_switch_view.o_pivot` dulu (CAND-05).

---

## Ringkasan Keseluruhan

| Step | Tipe | Jumlah AC |
|---|---|---|
| 04 | Unit | 12 |
| 04 | Integration | 20 |
| 04 | Smoke | 1 (AC-01-01 — install bersih) |
| 04 | API (kondisional) | N/A |
| 07 | AI-interaktif (`07` §3) | 8 |
| 07 | Tour headless (Mode E) | 4 (subset) |
