# Test Plan (Migrasi) — advanced_sales_analysis

**Step:** 5 — Acceptance Criteria & Test Plan (satu paket dengan `05a_MIGRATION_ACCEPTANCE_CRITERIA.md`)
**Ref:** `05_acceptance/05a_MIGRATION_ACCEPTANCE_CRITERIA.md`
**Tanggal:** 2026-08-26

---

## Step 9 — Dev Testing

> Eksekusi: **otomatis/background** — `odoo-bin -i advanced_sales_analysis --test-enable --test-tags /advanced_sales_analysis --stop-after-init`. Tidak ada Owl/JS/Tour (Fase E/F N/A, `01a_MIGRATION_INTAKE.md` §2b) — murni Unit/Integration. 38 test existing diwarisi dari migrasi 17→18 (`tests/`), dijalankan ulang terhadap environment 19.0 — bukan ditulis dari nol.

| AC | Deskripsi | Unit | Integration | Tour (N/A) |
|---|---|---|---|---|
| AC-01-01/02 | Instalasi & measure muncul | `test_sale_report.py` (install-time assertions) | — | N/A |
| AC-02-01..04 | Kolisi `amount_paid`/`account_payment` | `test_account_move.py::test_ac_02_*` | — | N/A |
| AC-03-01..04 | Komponen uang muka `account.move` | `test_account_move.py::test_ac_03_*` | — | N/A |
| AC-04-01..04 | `amount_received` (SO line) | `test_sale_order_line.py::test_ac_04_*` | — | N/A |
| AC-05-01..03 | `waiting_for_payment` (SO line) | `test_sale_order_line.py::test_ac_05_*` | — | N/A |
| AC-06-01..04 | `asa_amount_to_invoice` (SO line) | `test_sale_order_line.py::test_ac_06_*` | — | N/A |
| **AC-06-03b** (BARU) | Verifikasi fix DIFF-01 (`tax_id`→`tax_ids`) lewat jalur pajak `price_include` | `test_sale_order_line.py` — **method BARU wajib ditambahkan Step 6**, mis. `test_ac_06_03b_tax_ids_rename_price_include` | — | N/A |
| AC-07-01..04 | `sale.report` SQL view | `test_sale_report.py::test_ac_07_*` | `test_sale_report.py` (butuh `flush_all()`, lintas model) | N/A |
| AC-07-05 | UNION dengan POS (gap, belum tertutup) | — | **Tidak dieksekusi** — `point_of_sale`/`pos_sale` tidak terinstall di environment G1 standar. Tetap dicatat gap, bukan lulus. | N/A |

**Audit kesiapan test (Fase 9a, per `USAGE_GUIDE.md`):** test suite ini SUDAH execution-verified sekali (migrasi 17→18, 38/38 lulus, bukan stub kosong) — tidak perlu audit `ast` ulang dari nol seperti modul yang belum pernah dites, tapi WAJIB re-run penuh terhadap 19.0 (bukan diasumsikan lulus dari hasil lama) karena environment core berubah.

## Step 10 — QA Testing

| AC | Deskripsi | Manual | AI-interaktif | AI+tool eksternal |
|---|---|---|---|---|
| AC-01-02 | Measure muncul di UI pivot Sales Analysis | Checklist manual (`human_qa/`) | Kalau `Claude in Chrome` tersedia & server 19.0 hidup — cek cepat (histori Step 10 migrasi 17→18 mencatat SPA Odoo 18 gagal terbaca tool browser AI; kemungkinan sama untuk 19.0, verifikasi ulang, bukan diasumsikan gagal juga) | — |
| AC-06-03/AC-06-03b | Nilai numerik `asa_amount_to_invoice` di UI pivot (delivery policy, pajak inclusive) | Checklist manual — bandingkan angka pivot 19.0 vs referensi 18.0 | — | — |
| AC-07-03 | Granularitas baris laporan (2 row untuk kasus `price_unit` beda) | Checklist manual — hitung jumlah baris di pivot | — | — |

**Kalau `Claude in Chrome`/tool browser AI TIDAK bisa membaca DOM Odoo 19 SPA (pola yang sudah 3x terjadi di project sebelumnya untuk Odoo 18)** — mitigasi sama seperti sebelumnya: checklist manual `human_qa/` lengkap + bukti otomatis kuat dari Step 9, bukan diam-diam dilewati. Cek dulu `mcp__claude-in-chrome__list_connected_browsers` sebelum berasumsi tidak tersedia.

## Step 11 — UAT

| Kelompok fitur | AC tercakup | UAT |
|---|---|---|
| Instalasi bersih | AC-01 | Business user konfirmasi modul terinstall di instance UAT 19.0 tanpa error |
| Metrik finansial pivot (Amount Received/Waiting for Payment/Amount To Invoice) | AC-02 s.d. AC-07 | Business user (finance/sales manager) bandingkan angka pivot 19.0 vs 18.0 untuk data yang sama, konfirmasi identik (kecuali penyimpangan yang sudah disetujui: granularitas MF-01, rename field MF-02 — keduanya sudah baseline, bukan hal baru untuk migrasi ini) |

## Ringkasan

| Step | Role | Tipe | Eksekusi | Jumlah AC |
|---|---|---|---|---|
| 9 | Developer | Unit/Integration | Otomatis/background (38 test warisan + 1 test baru AC-06-03b) | 30 |
| 10 | QA | Manual (utama) + AI-interaktif (kalau tool browser AI bisa baca Odoo 19 SPA) | Campuran | 3 fokus verifikasi visual |
| 11 | PM/FA/User | UAT | Manual (selalu) | 2 kelompok fitur |
