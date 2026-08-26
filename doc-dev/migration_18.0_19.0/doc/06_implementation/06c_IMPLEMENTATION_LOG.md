# Implementation Log — advanced_sales_analysis

**Step:** 6 — Code Migration
**Ref:** `03_spec/03_MIGRATION_SPEC.md`, `migration-tool/templates/06a_CODE_MIGRATION_PHASES.md`
**Tanggal:** 2026-08-26

---

## Applicability Check

Dari `01a_MIGRATION_INTAKE.md` §2b (semua fase kondisional N/A — modul murni backend/compute, `'data': []`, tidak ada controller/asset/JS/relasi kompleks):

| Fase | Relevan? | Bukti/alasan (dari `01a` §2b) |
|---|---|---|
| C1 (View Sederhana) | ☐ Ya / **☑ Tidak** | `'data': []` — tidak ada view/XML sama sekali |
| B2 (Model Kompleks) | ☐ Ya / **☑ Tidak** | Semua field `Float` sederhana, tidak ada relasi berantai/JSON/dynamic model creation |
| C2 (Semantik XML & UX) | ☐ Ya / **☑ Tidak** | Otomatis N/A — C1 sudah N/A |
| D1 (Controllers) | ☐ Ya / **☑ Tidak** | `controllers/controllers.py` kosong, tidak ada route aktif |
| D2 (Assets & CSS) | ☐ Ya / **☑ Tidak** | Tidak ada `static/src/`, tidak ada key `assets` di manifest |
| E (JavaScript/Owl) | ☐ Ya / **☑ Tidak** | Tidak ada file `.js` |
| F (Upgrade Template) | ☐ Ya / **☑ Tidak** | Otomatis N/A — E sudah N/A |

Fase yang berlaku tanpa syarat: **A1-A5, B1** (semua modul punya manifest & model).

---

## Tabel Ringkas Status Fase

| Fase | Status | Tanggal |
|---|---|---|
| A1 | ✅ | 2026-08-26 |
| A2 | N/A — tidak ada XML | — |
| G1 #1 (setelah A1/A5, digabung — lihat catatan di bawah) | ⏳ Menunggu keputusan mode eksekusi dari dev | — |
| A3 | N/A — `security/ir.model.access.csv` fisik ada tapi entrinya di-comment di manifest sejak baseline (`[BSL-015]`), tidak ada model TransientModel baru yang butuh ACL | 2026-08-26 |
| A4 | ✅ — struktur folder (`models/`, `controllers/`, `security/`, `static/`, `tests/`) konsisten, `__init__.py` tidak berubah | 2026-08-26 |
| A5 | ✅ | 2026-08-26 |
| B1 | ✅ | 2026-08-26 |
| B2 | N/A — dikonfirmasi Applicability Check | — |
| C1 | N/A — dikonfirmasi Applicability Check | — |
| C2 | N/A — dikonfirmasi Applicability Check | — |
| D1 | N/A — dikonfirmasi Applicability Check | — |
| D2 | N/A — dikonfirmasi Applicability Check | — |
| E | N/A — dikonfirmasi Applicability Check | — |
| F | N/A — dikonfirmasi Applicability Check | — |
| G2 (validasi akhir/runtime) | ⏳ Menunggu G1 | — |

> **Catatan urutan:** modul ini tidak punya XML (A2 N/A) maupun ACL baru (A3 N/A) — dua blocker instalasi klasik yang biasanya jadi alasan G1 diulang 2x tidak relevan di sini. Satu-satunya perubahan yang benar-benar mempengaruhi instalasi/runtime adalah A5 (rename `tax_id`→`tax_ids`). G1 pertama dijalankan setelah A1+A5 selesai (digabung, bukan 2 titik terpisah seperti pola modul dengan XML/ACL) — cukup, karena tidak ada fase lain sebelumnya yang bisa mengubah hasilnya.

## Riwayat Percobaan G1 (Install Test)

> **Mode eksekusi belum ditentukan** — AI WAJIB menawarkan pilihan ke dev sebelum G1 pertama dijalankan (lihat `06a_CODE_MIGRATION_PHASES.md` "Checkpoint G1"), bukan berasumsi sepihak. Environment sesi ini: Claude Code CLI dengan shell persisten (Bash tool) — Mode C (AI jalankan langsung) TERSEDIA sebagai opsi kalau Docker Desktop dev sudah jalan dan `docker-env/docker-compose.yml` (warisan migrasi 17→18) masih valid untuk versi 19.0 (perlu dicek/disesuaikan image Odoo 19.0 dulu).

| # | Dijalankan setelah fase | Mode | Hasil | Error (kalau fail) | Tanggal |
|---|---|---|---|---|---|
| 1 | A1+A5 | *(menunggu keputusan dev — lihat pertanyaan di chat)* | — | — | — |

---

## Entri

## [Fase A1] Manifest Bootstrap

- **Scope:** `advanced_sales_analysis/__manifest__.py`
- **Item spec (ref):** `03_MIGRATION_SPEC.md` §2 baris 3, §2b Critical Blocker #1
- **Aksi:**
  - `__manifest__.py`: `'version': '18.0.1.0.0'` → `'19.0.1.0.0'`
- **Secara eksplisit TIDAK dilakukan:**
  - Tidak ada key manifest lain yang disentuh (`depends`, `data`, `license`, `price`, dst tetap apa adanya — semua dikonfirmasi tetap kompatibel di Step 2)
- **Risiko:** LOW
- **Status:** ✅ Selesai

## [Fase A5] Python API Compatibility (Models Only)

- **Scope:** `advanced_sales_analysis/models/sale_report.py`
- **Item spec (ref):** `03_MIGRATION_SPEC.md` §2 baris 1-2, §2b Critical Blocker #2 & Kompatibilitas Data Model #1 (ref `DIFF-01`)
- **Aksi:**
  - `models/sale_report.py:114`: `line.tax_id.filtered(lambda tax: tax.price_include)` → `line.tax_ids.filtered(lambda tax: tax.price_include)`
  - `models/sale_report.py:118`: `line.tax_id.compute_all(...)` → `line.tax_ids.compute_all(...)`
  - Tidak ada perubahan lain di method `_compute_asa_amount_to_invoice` — cabang logika (termasuk dead-code path F-17 yang dipertahankan sesuai `[BSL-008]`) TIDAK disentuh, murni rename accessor.
- **Secara eksplisit TIDAK dilakukan:**
  - Tidak memperbaiki dead-code path F-17 (`[BSL-008]`) — bukan scope migrasi ini
  - Tidak menyentuh `l.tax_ids` (baris invoice line, sudah benar sejak 18.0, bukan bagian rename ini)
  - Tidak menyentuh method lain (`_compute_amount_paid`, `_compute_amount_dp`, `_compute_waiting_for_payment_research`, `_compute_amount_received_research`) — dikonfirmasi Step 2 tidak terdampak
- **Risiko:** LOW (rename mekanis, dikonfirmasi tidak mengubah semantik pajak — `tax_ids` 19.0 adalah field yang SAMA persis secara semantik dengan `tax_id` 18.0, cuma nama berbeda)
- **Status:** ✅ Selesai

## [Fase B1] Model Risiko Rendah — Review Kelengkapan

- **Scope:** `advanced_sales_analysis/models/sale_report.py` (seluruh isi, review menyeluruh)
- **Item spec (ref):** `03_MIGRATION_SPEC.md` §2 baris 4
- **Aksi:**
  - Review `@api.depends` di semua method compute — tidak ada field yang direferensikan yang berubah nama/hilang di 19.0 selain `tax_id` (sudah ditangani A5). Field yang dipakai di `@api.depends` (`amount_residual`, `invoice_line_ids`, `payment_state`, `move_type`, `state`, `product_id`, `untaxed_amount_invoiced`, `qty_delivered`, `product_uom_qty`, `order_id`, `invoice_lines`, `product_template_id`, `discount`, `currency_id`, `company_id`) — semua dikonfirmasi stabil di Step 2 (DIFF-06, tabel API surface).
  - Tidak ada perubahan kode tambahan diperlukan — modul sudah lengkap setelah A1+A5.
- **Secara eksplisit TIDAK dilakukan:**
  - Tidak ada refactor/pembersihan dependency compute yang sudah ada (bukan scope migrasi, lihat `[BSL-021]` @api.depends melingkar yang sengaja dipertahankan)
- **Risiko:** LOW
- **Status:** ✅ Selesai

## [Prep G1] Update `docker-env/` untuk target 19.0

- **Scope:** `docker-env/Dockerfile`, `docker-env/docker-compose.yml`
- **Item spec (ref):** prasyarat Checkpoint G1 (`06a_CODE_MIGRATION_PHASES.md`), bukan bagian fase A1-B1 itu sendiri
- **Aksi:**
  - `Dockerfile`: `FROM odoo:18.0` → `FROM odoo:19.0`. **Belum diverifikasi eksekusi** (tidak ada akses jaringan di sesi ini untuk cek tag Docker Hub) — kalau `docker compose build` gagal pull image, ini indikasi tag salah/belum ada, bukan bug Dockerfile lain.
  - `docker-compose.yml`: `name:` → `advanced_sales_analysis_migration_19` (hindari collide container project 17→18), volume mount path diarahkan ke folder ini (`advanced-sales-analysis-migration-19`, bukan folder lama `advanced_sales_analysis-migration-18`), `-d` database name → `advanced_sales_analysis_test_19`, host port `8077`→`8078` (hindari collide kalau container 18.0 masih hidup).
- **Secara eksplisit TIDAK dilakukan:**
  - Tidak menyentuh pola fallback `pip3 install --break-system-packages ... || ...` (dipertahankan apa adanya dari versi 18.0, belum dikonfirmasi masih perlu di 19.0)
  - Tidak menghapus/mengubah volume `db-data`/`odoo-data` (biarkan persist sesuai desain lama)
- **Risiko:** MEDIUM (tag image 19.0 belum diverifikasi tersedia — kegagalan di titik ini adalah kegagalan environment/infra, bukan kegagalan kode modul)
- **Status:** ✅ Selesai (edit file) — efeknya baru diketahui saat G1 benar-benar dijalankan

## [Fase A2] N/A — dikonfirmasi Applicability Check (tidak ada view/XML)
## [Fase A3] N/A — dikonfirmasi Applicability Check (tidak ada TransientModel/ACL baru)
## [Fase B2] N/A — dikonfirmasi Applicability Check
## [Fase C1] N/A — dikonfirmasi Applicability Check
## [Fase C2] N/A — dikonfirmasi Applicability Check
## [Fase D1] N/A — dikonfirmasi Applicability Check
## [Fase D2] N/A — dikonfirmasi Applicability Check
## [Fase E] N/A — dikonfirmasi Applicability Check
## [Fase F] N/A — dikonfirmasi Applicability Check

## [Test] AC-06-03b — Test baru wajib (`05b_TEST_PLAN_MIGRATION.md`)

- **Scope:** `advanced_sales_analysis/tests/test_sale_order_line.py`
- **Item spec (ref):** `05a_MIGRATION_ACCEPTANCE_CRITERIA.md` AC-06-03b
- **Aksi:**
  - Tambah `test_ac_06_03b_tax_ids_rename_price_include`: buat pajak `price_include_override='tax_included'` 10%, assign ke produk baru, buat SO, baca `asa_amount_to_invoice` — verifikasi TIDAK `AttributeError` dan hasil numerik benar (`100.0` dari gross `110.0` dikurangi pajak included 10%, via cabang "else"/`line.price_subtotal` yang sudah tax-excluded otomatis oleh core — bukan dari `price_subtotal` lokal yang dihitung `tax_ids.compute_all()`, yang tetap DISCARDED oleh dead-code path F-17 sesuai `[BSL-008]`, TAPI baris kode itu tetap WAJIB tereksekusi tanpa error karena dipanggil unconditional sebelum percabangan).
  - Field/method baru yang dipakai test: `account.tax` (`price_include_override`, `amount_type='percent'`), `product.product.taxes_id`. Tidak menyentuh `common.py` (self-contained di dalam method test).
- **Secara eksplisit TIDAK dilakukan:**
  - Tidak menguji skenario discount-mismatch (`inv_lines.mapped(lambda l: l.discount != line.discount)`) sekaligus — itu akan menguji jalur `l.tax_ids` (account.move.line, TIDAK terdampak DIFF-01) bercampur dengan jalur `line.tax_ids` (sale.order.line, TERDAMPAK) dalam satu test, mengurangi kejelasan apa yang sebenarnya diverifikasi. Dipisah demi kejelasan sinyal test, bukan celah cakupan (jalur discount-mismatch sendiri sudah tercakup AC-06-03/`test_ac_06_04_invoice_policy_delivery_diabaikan` tanpa pajak).
- **Risiko:** LOW
- **Status:** ✅ Selesai (kode ditulis) — **belum dieksekusi**, menunggu G1

---

## Temuan di Luar Spec

- [x] Tidak ada — semua perubahan sesuai `03_MIGRATION_SPEC.md`, tidak ada penemuan baru di luar yang sudah diidentifikasi Step 2/3.

## Kontribusi ke Knowledge Base

- [x] Tidak ada temuan baru yang perlu dicatat di fase ini — temuan DIFF-01 sudah dicatat di `migration-records/advanced_sales_analysis_18.0_19.0/SUMMARY.md` CAND-01 sejak Step 2.
