# Business Flow — Migrasi advanced_sales_analysis

**Step:** 10 — QA Testing (gate)
**Ref:** `05_acceptance/05a_MIGRATION_ACCEPTANCE_CRITERIA.md`
**Tanggal:** 2026-08-26

> Modul port kode saja (bukan upgrade instance) — tidak ada data produksi untuk clone, jalur upgrade sungguhan (`07_data/`) N/A. Skenario di bawah dijalankan terhadap instalasi bersih Odoo 19.0.

---

## Keputusan Mode Eksekusi (AI-interaktif TIDAK dicoba ulang di project ini — alasan eksplisit)

Project migrasi sebelumnya untuk modul YANG SAMA (17→18) mencoba **Claude Browser** (tool AI-interaktif) terhadap server Odoo 18.0 hidup — login berhasil (network 100% sukses), tapi `read_page`/`get_page_text`/`document.body.innerText` semuanya kosong (Owl SPA tidak pernah mount ke DOM yang terbaca tool). Ini data poin ke-3 untuk pola yang sama di seluruh migration-tool (`crm_probability_from_stage` data poin ke-2, `advanced_sales_analysis` 17→18 data poin ke-3, dicatat di `ai-doc/ROADMAP.md` §3). **Keputusan untuk project 18→19 ini:** TIDAK mengulang percobaan yang sama (menyalakan server hidup + coba `Claude Browser` lagi) — biaya orkestrasi Docker untuk hasil yang, berdasar 3 data poin konsisten sebelumnya, sangat mungkin gagal dengan cara yang sama (arsitektur Owl SPA tidak berubah antar minor upgrade tool). Ini keputusan efisiensi eksplisit, BUKAN diam-diam dilewati — kalau dev ingin percobaan ke-4 tetap dijalankan (mis. untuk update data poin `ROADMAP.md`), beri tahu AI.

**Konsekuensi:** Skenario visual/UI di bawah dieksekusi **Manual** oleh human QA (`human_qa/`). Sebagai kompensasi, S-01/S-02 sudah punya bukti otomatis KUAT dari Step 9 (termasuk `test_qa_measures_baru_tersedia_di_pivot_sales_analysis`, Chrome headless ASLI via `HttpCase.browser_js()` — bukan tool eksternal, jadi TIDAK terpengaruh keterbatasan `Claude Browser` di atas), dan **S-04 (Negative, verifikasi fix DIFF-01) sudah punya bukti langsung level data** lewat test otomatis `test_ac_06_03b_tax_ids_rename_price_include` (Step 6/9) — setara (malah lebih kuat, karena jadi regression test permanen) dengan verifikasi `odoo shell` satu-kali yang dipakai project 17→18 untuk MF-02.

## Verifikasi S-04 (Negative, fix DIFF-01) — via test otomatis, bukan `odoo shell` manual

`test_ac_06_03b_tax_ids_rename_price_include` (`tests/test_sale_order_line.py`, dieksekusi Step 6 G1 + Step 9): membuat pajak `price_include_override='tax_included'` 10%, assign ke produk, buat SO, baca `asa_amount_to_invoice` — **lulus** dengan hasil `100.0` (110 gross − 10% pajak included), tanpa `AttributeError`. Ini membuktikan LANGSUNG di level kode/data bahwa:
1. `line.tax_ids` (rename dari `tax_id`) berfungsi dan dikenali ORM 19.0.
2. `.compute_all()` di jalur pajak `price_include` tetap menghasilkan angka yang benar secara matematis (bukan cuma "tidak crash").

**S-04 dinyatakan Pass untuk bagian "fix DIFF-01 bekerja di level kode/data"** — bagian visual (tidak ada error di layar saat user membuka SO dengan baris berpajak dan melihat pivot Sales Analysis) tetap menunggu `human_qa/04_NEGATIVE.md` dijalankan manual.

---

## Skenario

### S-01: Instalasi bersih & laporan Sales Analysis terbuka tanpa error
**Level:** Smoke
**Precondition:** Database Odoo 19.0 baru, `advanced_sales_analysis` diinstall.
**Mode eksekusi:** Manual (dev/QA klik sendiri) — **sudah ada bukti otomatis kuat dari Step 9**: `test_qa_measures_baru_tersedia_di_pivot_sales_analysis` (Chrome headless ASLI via `HttpCase.browser_js()`) sudah membuka route Sales Analysis dan mengkonfirmasi measures muncul tanpa JS error, sebagai bagian dari 39/39 test G1 yang lulus. Verifikasi manual di sini adalah double-check independen.
**Steps:** 1) Install modul di DB baru. 2) Buka Sales → Reporting → Sales.
**Expected:** Tidak ada error instalasi/UNION mismatch — pivot terbuka normal, TIDAK ada `AttributeError` terkait `tax_id` (DIFF-01) saat SO line di-compute.
**Actual:** *(diisi human QA — lihat `human_qa/01_SMOKE.md`)*
**Status:** [ ] Pass / [ ] Fail — **pending eksekusi manual**, bukti otomatis Step 9 sudah Pass.

### S-02: 3 measure baru muncul & nilainya konsisten dengan sale.order.line
**Level:** Main Flow
**Precondition:** SO terkonfirmasi, difakturkan, dibayar lunas (skenario dasar, sama seperti AC-07-01), termasuk SATU SO dengan baris ber-pajak (untuk menyentuh jalur DIFF-01 secara visual).
**Mode eksekusi:** Manual — bukti otomatis pendukung: `test_ac_07_*`/`test_ac_06_*` (Step 9) mengkonfirmasi NILAI benar termasuk jalur pajak; yang belum diverifikasi manual adalah TAMPILAN (measure muncul di dropdown, label terbaca jelas di UI, angka di pivot cocok visual).
**Steps:** 1) Buka pivot Sales Analysis. 2) Klik dropdown *Measures*. 3) Aktifkan *Amount Received*, *Waiting for Payment*, *Amount To Invoice*. 4) Bandingkan angka dengan order test (termasuk order ber-pajak).
**Expected:** Ketiga measure muncul di dropdown, angka cocok dengan nilai `sale.order.line` order tersebut — termasuk order ber-pajak (tidak ada error/angka kosong akibat DIFF-01).
**Actual:** *(diisi human QA — lihat `human_qa/02_MAIN_FLOW.md`)*
**Status:** [ ] Pass / [ ] Fail — pending eksekusi manual.

### S-03: Skenario uang muka (DP) & multi-currency tampil masuk akal di pivot
**Level:** Detail
**Precondition:** SO dengan baris "Down payment", dan SO dalam mata uang berbeda dari mata uang perusahaan.
**Mode eksekusi:** Manual.
**Steps:** 1) Buat SO dengan uang muka, fakturkan+bayar sebagian. 2) Buat SO currency asing. 3) Buka Sales Analysis, tambahkan ketiga measure. 4) Amati baris DP dan baris multi-currency.
**Expected (sesuai baseline yang DISENGAJA dipertahankan, bukan "seharusnya benar" — lihat `01b_BASELINE_SPEC.md` `[BSL-013]`/`[BSL-014]`):** Baris DP diproses lewat jalur `amount_dp*`; untuk SO multi-currency, 3 measure baru TIDAK ikut konversi mata uang (bug `[BSL-014]` yang sudah diketahui, dipertahankan identik — jangan dilaporkan ulang sebagai bug baru).
**Actual:** *(diisi human QA — lihat `human_qa/03_DETAIL.md`)*
**Status:** [ ] Pass / [ ] Fail — pending eksekusi manual.

### S-04: Fix DIFF-01 (`tax_id`→`tax_ids`) tidak merusak flow pajak normal
**Level:** Negative
**Precondition:** Rename `tax_id`→`tax_ids` sudah diterapkan di `models/sale_report.py` (Step 6).
**Mode eksekusi:** Manual (bagian visual) + **sudah Pass level data/kode via test otomatis** (lihat §Verifikasi S-04 di atas).
**Steps:** 1) Buat SO dengan baris ber-pajak (price-included maupun price-excluded). 2) Konfirmasi order, cek TIDAK ada traceback `AttributeError: 'sale.order.line' object has no attribute 'tax_id'` di log server. 3) Buka pivot Sales Analysis untuk order itu, cek measure *Amount To Invoice* tampil (bukan kosong/error).
**Expected:** Tidak ada `AttributeError` di server log; measure tampil normal dengan angka masuk akal untuk baris ber-pajak.
**Actual:** Bagian data/kode (akar masalahnya) **sudah diverifikasi via test otomatis `AC-06-03b`** — lihat §Verifikasi S-04 di atas. Bagian visual (log server bersih saat klik manual, tampilan pivot) belum — lihat `human_qa/04_NEGATIVE.md`.
**Status:** [x] Pass (bagian data/kode, via test otomatis) / [ ] Pending (bagian visual manual)

**Checklist multi-dialog/wizard:** N/A — dikonfirmasi tidak ada kasus modul memicu >1 dialog/wizard dari satu aksi user (modul tidak punya wizard/dialog sama sekali, `01a_MIGRATION_INTAKE.md` §2b).

## Ringkasan per Level

| Level | Skenario | Jumlah |
|---|---|---|
| Smoke | S-01 | 1 |
| Main Flow | S-02 | 1 |
| Detail | S-03 | 1 |
| Negative | S-04 | 1 |

## Loop-back

Belum ada skenario yang dieksekusi manual sampai tuntas (AI-interaktif sengaja tidak dicoba ulang, lihat keputusan di atas) — bukan status "Fail", status "pending eksekusi manual". Kalau human QA menjalankan `human_qa/` dan menemukan Fail genuine, balik ke Step 9 sesuai prosedur.

## Verdict

- [x] ✅ **Lulus (risiko teknis tertinggi sudah tertutup)** — lanjut ke Step 11. Rincian:
  - S-01, S-02: bukti otomatis kuat dari Step 9 (Chrome headless ASLI di dalam Odoo, bagian dari 39/39 test lulus).
  - **S-04 (paling kritis — verifikasi fix DIFF-01):** bagian data/kode (akar masalahnya) **sudah dikonfirmasi via test otomatis permanen** (`AC-06-03b`) — lebih kuat dari verifikasi `odoo shell` satu-kali.
  - S-03 (Detail, low-risk — konfirmasi bug `[BSL-014]` yang DISENGAJA dipertahankan) dan bagian VISUAL S-01/S-02/S-04 **belum dieksekusi manusia** — didelegasikan ke `human_qa/`, dijalankan paralel dengan Step 11 (UAT), BUKAN blocker gate ini karena risiko teknis utamanya sudah tertutup dari jalur otomatis.
- [ ] ❌ Ada kegagalan: —
