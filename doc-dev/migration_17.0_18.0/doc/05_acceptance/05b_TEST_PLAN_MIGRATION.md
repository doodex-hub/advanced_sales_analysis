# Test Plan (Migrasi) — advanced_sales_analysis

**Step:** 5 — Acceptance Criteria & Test Plan (satu paket dengan `05a_MIGRATION_ACCEPTANCE_CRITERIA.md`)
**Ref:** `05_acceptance/05a_MIGRATION_ACCEPTANCE_CRITERIA.md`
**Tanggal:** 2026-08-21

> **Audit kesiapan test (WAJIB dicek sebelum tabel di bawah dipercaya, per peringatan `USAGE_GUIDE.md` §5):**
> 38 method test di `source-codebase/advanced_sales_analysis/tests/` (`test_account_move.py`=13,
> `test_sale_order_line.py`=17, `test_sale_report.py`=7, `test_qa_browser.py`=1) diaudit lewat
> `grep -c "self\.assert"` per file — **71 assertion ditemukan total, tersebar di ketiga file unit/integration**
> (13/26/32 kira-kira, dicek langsung bukan cuma nama method) — bukan stub docstring seperti kasus
> `totp_enhancement`. Dikonfirmasi juga: jumlah method (38) cocok dengan angka "38 test" yang disebut
> `FINDINGS.md`/riwayat commit backfill (`e3ef156`) — konsisten, bukan drift. Test-test ini SUDAH
> pernah dijalankan nyata terhadap 17.0 (bukan sekadar ditulis) — Step 9 project ini tinggal RE-RUN
> terhadap 18.0, bukan menulis dari nol.

---

## Step 9 — Dev Testing

> Eksekusi: **otomatis/background** — `odoo-bin -i advanced_sales_analysis --test-enable --test-tags /advanced_sales_analysis --stop-after-init` terhadap image `odoo:18.0`. **PENTING (Windows Git Bash/MSYS):** prefix `MSYS_NO_PATHCONV=1` WAJIB di command ini — tanpa itu, argumen `/advanced_sales_analysis` bisa dikonversi jadi path Windows dan tag filter jadi kosong, menghasilkan false-pass "0 failed, 0 error(s) of 0 tests" (lihat lesson `crm_probability_from_stage`, `migration-records/`). **Verifikasi WAJIB:** cocokkan jumlah `Starting <Class>.<method>` di log dengan 38 method di bawah — jangan cuma percaya exit code.
>
> Tidak ada Tour test (Owl/JS) — modul tidak punya komponen JS (`01a_MIGRATION_INTAKE.md` §2b).

| AC | Deskripsi | Unit/Integration (method test, `source-codebase`) | Tour (Owl/JS) |
|---|---|---|---|
| AC-01-01, AC-01-03 (`[BSL-005]`,`[BSL-006]`) | Instalasi bersih, kolom terdaftar, kolisi `amount_paid` menang sesuai baseline | `test_ac_01_03_account_payment_terinstall_bersama`, `test_ac_01_03_definisi_amount_paid_yang_menang`, `test_ac_01_03_semantik_amount_paid_bukan_semantik_account_payment` | N/A |
| AC-02-02..04 (`[BSL-006]`) | `amount_paid`/`amount_paid_cn` per skenario `move_type`/`payment_state` | `test_ac_02_01_amount_paid_out_invoice_lunas`, `test_ac_02_02_amount_paid_cn_out_refund_lunas`, `test_ac_02_03_move_type_entry_tidak_assign`, `test_ac_02_04_out_invoice_belum_dibayar_tidak_assign` | N/A |
| AC-03-01..04 (`[BSL-007]`,`[BSL-011]`,`[BSL-013]`) | 6 field komponen DP, last-row-wins, partial-not-counted, hardcoded string non-English | `test_ac_03_01_dp_positif_belum_dibayar`, `test_ac_03_02_dp_negatif_sudah_dibayar`, `test_ac_03_03_dua_baris_dp_hanya_yang_terakhir_menang`, `test_ac_03_04_dp_terbayar_sebagian_dianggap_belum_dibayar`, `test_ac_03_05_produk_dp_non_inggris_tidak_dikenali` | N/A |
| (structural, ref `[BSL-017]`) | Label field duplikat memicu WARNING instalasi | `test_f13_label_field_duplikat` | N/A |
| AC-04-01..04 (`[BSL-010]`,`[BSL-020]`) | `amount_received` per skenario pembayaran/DP/untaxed-nol | `test_ac_04_01_received_penuh`, `test_ac_04_02_received_nol_kalau_belum_dibayar`, `test_ac_04_03_received_pembayaran_sebagian`, `test_ac_04_04_received_proporsional_dua_baris`, `test_ac_04_05_credit_note_mengurangi_received`, `test_ac_04_06_baris_dp_pakai_jalur_amount_dp`, `test_ac_04_07_faktur_untaxed_nol_tidak_error` | N/A |
| AC-05-01..03 (`[BSL-009]`) | `waiting_for_payment` per skenario pembayaran/cancel/multi-faktur | `test_ac_05_01_waiting_penuh`, `test_ac_05_02_waiting_setelah_pembayaran_sebagian`, `test_ac_05_03_waiting_nol_kalau_belum_difakturkan`, `test_ac_05_04_faktur_cancel_diabaikan`, `test_ac_05_05_dua_faktur_untuk_satu_baris_so` | N/A |
| AC-06-01..03 (`[BSL-008]`) | `amount_to_invoice` kasus dasar | `test_ac_06_01_to_invoice_sebelum_difakturkan`, `test_ac_06_02_to_invoice_setelah_lunas`, `test_ac_06_03_to_invoice_nol_kalau_draft` | N/A |
| **AC-06-03 kritis** (`[BSL-008]`, F-17) | `invoice_policy == 'delivery'` diabaikan — regresi paling penting untuk dideteksi | `test_ac_06_04_invoice_policy_delivery_diabaikan` — **hasil HARUS `100.0`, kalau `40.0` itu regresi, eskalasi segera** | N/A |
| **AC-06-04** (`[BSL-021]`, DIFF-06 — status belum pasti) | `@api.depends` melingkar tidak menyebabkan order-dependency | `test_ac_06_05_urutan_pembacaan_field_melingkar` — **WAJIB dijalankan & hasilnya dicatat eksplisit di §Verdict di bawah**, ini item yang menutup gap DIFF-06 | N/A |
| AC-07-01, 02 (`[BSL-005]`) | Nilai `sale.report` cocok dengan `sale.order.line`, guard `product_id IS NOT NULL` | `test_ac_07_01_kolom_baru_cocok_dengan_baris_so`, `test_ac_07_01b_waiting_dan_to_invoice_muncul_di_laporan`, `test_ac_07_01c_flush_wajib_sebelum_query`, `test_ac_07_02_baris_tanpa_product_id` | N/A |
| **AC-07-03** (`[BSL-023]`, MF-01 — penyimpangan disetujui) | Granularitas 18.0 (2 baris untuk `price_unit` berbeda) BEDA dari 17.0 (1 baris) secara disengaja — core Odoo berubah, disetujui pemilik modul | `test_ac_07_03_group_by_granularitas_18_0` (di-rename + assertion diperbarui 2026-08-21, lihat `FINDINGS.md` MF-01) | N/A |
| **AC-07-05** (`[BSL-005]`, gap testing) | UNION tetap sinkron kalau `point_of_sale` ikut terinstall | `test_f19_union_kompatibel_dengan_point_of_sale` — **di backfill 17.0 test ini DI-SKIP** (POS tidak terinstall di image `odoo:17.0` yang dipakai). Kalau image `odoo:18.0` yang dipakai Step 9 SUDAH menyertakan `point_of_sale`, jalankan test ini sungguhan (bukan skip) — kesempatan menutup gap yang belum pernah tertutup di 17.0 sekalipun | N/A |
| AC-07-04 (`[BSL-014]`) | Kolom baru tidak dikonversi mata uang | `test_ac_07_04_kolom_baru_tidak_dikonversi_mata_uang` | N/A |
| (QA, ref AC-01-02) | Measures baru muncul di pivot UI | `test_qa_measures_baru_tersedia_di_pivot_sales_analysis` (`test_qa_browser.py` — `HttpCase.browser_js()`, bukan Tour resmi karena manifest tidak punya `assets`, lihat `[BSL-022]`) | N/A (browser_js, bukan tour) |

### §Verdict Step 9 (diisi setelah eksekusi nyata — JANGAN diisi dari analisis dokumen)

- [ ] Jumlah test yang benar-benar START (grep log `Starting <Class>.<method>`) == 38 — dicocokkan, bukan diasumsikan.
- [ ] Hasil `test_ac_06_04_invoice_policy_delivery_diabaikan`: ... (harus `100.0`)
- [ ] Hasil `test_ac_06_05_urutan_pembacaan_field_melingkar`: ... (menutup gap DIFF-06)
- [ ] Hasil `test_f19_union_kompatibel_dengan_point_of_sale`: ... (skip atau jalan sungguhan, tergantung image)
- [ ] Verdict keseluruhan: ... failed, ... error dari 38 tests

---

## Step 10 — QA Testing

| AC | Deskripsi | Manual | AI-interaktif | AI+tool eksternal |
|---|---|---|---|---|
| AC-01-02 | Measure baru muncul di pivot Sales Analysis UI | — | Claude in Chrome: buka Sales Analysis, tambah measure, screenshot | — |
| AC-07-01 s/d 04 | Angka laporan pivot konsisten dengan nilai `sale.order.line` untuk skenario representatif (lunas, partial, DP, multi-currency) | Dev/QA menjalankan 1 skenario end-to-end manual di UI sebagai sanity-check tambahan di luar unit test | Opsional, kalau ingin verifikasi visual tambahan | Tidak perlu — Step 9 sudah cover lewat unit/integration test, ini murni sanity-check UI |

**Catatan:** karena modul ini murni backend/compute + SQL view (tidak ada custom UI/wizard), cakupan utama migrasi ada di Step 9 (unit/integration test) — Step 10 cukup sanity-check visual ringan, bukan re-test seluruh AC secara manual.

## Step 11 — UAT

| Kelompok fitur | AC tercakup | UAT |
|---|---|---|
| Sales Analysis — 3 metrik finansial baru | AC-01, AC-07 | Business user (finance/sales manager) membuka Sales Analysis di instance 18.0, menambah 3 measure, membandingkan angka dengan laporan 17.0 untuk periode/data yang sama — konfirmasi angka identik |
| Perhitungan komponen faktur (dibayar/DP/sisa tagih) | AC-02 s/d AC-06 | Business user (finance) mengecek 1-2 invoice riil dengan skenario DP/partial payment, konfirmasi angka `amount_paid`/`amount_dp*` konsisten dengan pemahaman bisnis (termasuk kesadaran bug F-01/F-04/F-17 yang dipertahankan sengaja, bukan tanpa sepengetahuan business user) |

---

## Ringkasan

| Step | Role | Tipe | Eksekusi | Jumlah AC |
|---|---|---|---|---|
| 9 | Developer | Unit/Integration (38 method existing, re-run terhadap 18.0) | Otomatis/background | 22 dari 29 AC (`AC-01` s/d `AC-07`, minus AC-01-02 QA-only) |
| 10 | QA | Manual + AI-interaktif (Claude in Chrome) | Campuran, sanity-check ringan | 5 AC (AC-01-02, AC-07-01..04) |
| 11 | PM/FA/User | UAT | Manual (selalu) | 2 kelompok fitur (mencakup seluruh 29 AC) |
