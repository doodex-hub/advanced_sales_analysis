# Implementation Log — advanced_sales_analysis

**Step:** 6 — Code Migration
**Ref:** `03_spec/03_MIGRATION_SPEC.md`, `migration-tool/templates/06a_CODE_MIGRATION_PHASES.md`
**Tanggal:** 2026-08-21

---

## Applicability Check

Sumber: `01_intake/01a_MIGRATION_INTAKE.md` §2b — semua baris "Ada di modul?" = Tidak.

| Fase | Relevan? | Bukti/alasan (dari `01a` §2b) |
|---|---|---|
| B2 — Model Kompleks | ☐ Ya / ☑ Tidak | Tidak ada field JSON/relasi berantai/dynamic model creation — semua field `Float` sederhana |
| C2 — Semantik XML & UX | ☐ Ya / ☑ Tidak | Tidak ada view sama sekali (`'data': []`) |
| D1 — Controllers | ☐ Ya / ☑ Tidak | `controllers/controllers.py` kosong (2 baris komentar), tidak ada route aktif |
| D2 — Assets & CSS | ☐ Ya / ☑ Tidak | Tidak ada key `assets` di manifest, tidak ada `static/src/css` |
| E — JavaScript (Owl) | ☐ Ya / ☑ Tidak | Tidak ada file `.js` di `static/src/` |
| F — Upgrade Template | ☐ Ya / ☑ Tidak | Otomatis N/A karena E juga N/A |

**Catatan tambahan (di luar tabel standar template — modul ini kasus tepi):** `06a_CODE_MIGRATION_PHASES.md` menyatakan Fase A1-A5 dan B1 "berlaku untuk modul apapun tanpa syarat (semua modul punya manifest, model, dan **minimal satu view**)". **Modul ini adalah pengecualian dari asumsi itu** — `'data': []`, tidak ada view/XML sama sekali. Konsekuensi: **Fase C1 (View Sederhana) juga N/A**, bukan cuma C2 — dicatat eksplisit di sini karena tidak ada baris untuk C1 di tabel Applicability Check standar (template mengasumsikan C1 selalu relevan). Kandidat catatan untuk `migration-records/` (lihat §Kontribusi ke Knowledge Base di bawah).

---

## Tabel Ringkas Status Fase

| Fase | Status | Tanggal |
|---|---|---|
| A1 | ✅ | 2026-08-21 |
| A2 | N/A — tidak ada XML sama sekali | 2026-08-21 |
| G1 #1 (setelah A2) | ❌ Fail (Dockerfile, bukan kode modul — lihat Riwayat Percobaan G1) → retry #2 | 2026-08-21 |
| A3 | N/A — tidak ada model baru/wizard yang butuh ACL (lihat entry A3 di bawah) | 2026-08-21 |
| A4 | ✅ | 2026-08-21 |
| A5 | ✅ — tidak ada perubahan (dikonfirmasi Step 2, semua API stabil) | 2026-08-21 |
| G1 #2 (setelah A3) | ✅ **Pass** (setelah percobaan #3 di tabel Riwayat G1 — MF-01 diputuskan Opsi 1, test disesuaikan) — 0 failed, 0 error(s) of 38 tests | 2026-08-21 |
| B1 | ✅ | 2026-08-21 |
| B2 | N/A — dikonfirmasi Applicability Check | — |
| C1 | N/A — tidak ada view sama sekali (lihat catatan Applicability Check) | — |
| C2 | N/A — dikonfirmasi Applicability Check | — |
| D1 | N/A — dikonfirmasi Applicability Check | — |
| D2 | N/A — dikonfirmasi Applicability Check | — |
| E | N/A — dikonfirmasi Applicability Check | — |
| F | N/A — dikonfirmasi Applicability Check | — |
| G2 (validasi akhir/runtime) | ✅ — kriteria minimal sudah terpenuhi lewat G1 percobaan #3 (lihat entri G2 di bawah, tidak perlu sesi browser terpisah) | 2026-08-21 |

## Riwayat Percobaan G1 (Install Test)

**Mode eksekusi:** C — AI jalankan langsung (Claude Code CLI, shell persisten, sesuai `CLAUDE.md` "Environment eksekusi").

**Setup:** `docker-env/Dockerfile` diubah `FROM odoo:17.0` → `FROM odoo:18.0`; `docker-env/docker-compose.yml` volume mount diarahkan ke `advanced_sales_analysis/` di DALAM `target-codebase` ini (sebelumnya menunjuk clone backfill lama `advanced-sales-analysis-17`, sisa instantiasi doc-dev-backfill sebelum project migrasi ini dimulai); `name:` project di-rename `advanced_sales_analysis_migration_18` supaya tidak collide dengan container backfill lama.

| # | Dijalankan setelah fase | Mode | Hasil | Error (kalau fail) | Tanggal |
|---|---|---|---|---|---|
| 1 | A1 (A2/A3 N/A, jadi G1 #1 dan #2 digabung menjadi satu run) | C | ❌ Fail — build image gagal (belum sampai ke tahap Odoo install) | `pip3 install websocket-client` → `error: externally-managed-environment` (PEP 668) di `docker-env/Dockerfile`. Root cause: Dockerfile project ini diinstansiasi dari versi `doc-dev-backfill` (2026-08-18, target 17.0) TANPA pola fallback `--break-system-packages \|\| ` yang SUDAH terdokumentasi di `migration-tool/templates/Dockerfile.template` (lesson 2026-07-29 `purchase_product_optional`) — image 17.0 (Ubuntu lama) tidak butuh flag itu, image 18.0 (Ubuntu lebih baru) mewajibkannya. **Fix:** Dockerfile diedit, tambah fallback `(pip3 install --break-system-packages websocket-client \|\| pip3 install websocket-client)`. | 2026-08-21 |
| 2 | A1 (retry setelah fix Dockerfile) | C | ❌ Fail — build sukses, Odoo terinstall, TAPI 1 dari 38 test gagal | `test_ac_07_03_group_by_tidak_lagi_memecah_baris`: `AssertionError: 2 != 1`. **Bukan bug kode modul** — root cause dikonfirmasi di `FINDINGS.md` MF-01: core `sale.report._group_by_sale()` 18.0 menambah kolom GROUP BY (`price_unit`, `invoice_status`, `is_downpayment`) dibanding 17.0, mengubah granularitas laporan independen dari modul ini. **BLOCKING — eskalasi ke user, lihat `FINDINGS.md` MF-01**, G1 belum bisa dinyatakan lulus sampai keputusan diambil. | 2026-08-21 |
| 3 | A1 (setelah user setuju Opsi 1 MF-01, test diperbaiki — tidak ada rebuild, cuma file test bind-mount) | C | ✅ **Pass** — `0 failed, 0 error(s) of 38 tests`. `test_ac_07_03_group_by_granularitas_18_0` (nama baru) lulus. `test_qa_measures_baru_tersedia_di_pivot_sales_analysis` (Chrome headless asli via `browser_js`) juga lulus — "test successful" dikonfirmasi di log, bukan cuma nama method ada. `test_f19_union_kompatibel_dengan_point_of_sale` tetap **di-skip** (`point_of_sale` tidak terinstall di image `odoo:18.0` ini juga, sama seperti 17.0) — gap AC-07-05 masih terbuka, dicatat, bukan blocker G1. | 2026-08-21 |
| 4 | Step 8 Code Review menemukan MF-02 (kolisi `amount_to_invoice` dengan field BARU core 18.0) — `models/sale_report.py` diedit (rename field+method), test disesuaikan | C | ✅ **Pass** — `0 failed, 0 error(s) of 38 tests`. Tidak ada warning baru (tipe field/label) akibat rename — cuma warning F-13 lama, sekarang menyebut `asa_amount_to_invoice` (konsisten, bukan regresi baru). | 2026-08-21 |

---

## Entri

## [Fase A1] Manifest Bootstrap

- **Scope:** `advanced_sales_analysis/__manifest__.py`
- **Item spec (ref):** `03_spec/03_MIGRATION_SPEC.md` §2b Critical Migration Blocker #1
- **Aksi:**
  - `__manifest__.py`: `'version': '17.0.1.0.0'` → `'version': '18.0.1.0.0'`
- **Secara eksplisit TIDAK dilakukan:**
  - Tidak ada perubahan `depends` (keempat dependency dikonfirmasi ada di 18.0, `01a` §2)
  - Tidak ada perubahan `data` (tetap `[]`, entri ACL tetap di-comment — F-07 dipertahankan)
  - Tidak ada perubahan `website` (tetap string URL, bukan boolean — field ini memang dimaksudkan string di manifest Odoo, bukan kasus yang disebut A1 "website string→boolean")
- **Risiko:** LOW
- **Status:** ✅ Selesai

## [Fase A2] N/A — dikonfirmasi Applicability Check (tidak ada XML/view sama sekali di modul ini)

## [Fase A3] N/A — dikonfirmasi tidak relevan

- **Alasan (bukan dari tabel Applicability Check standar — dicatat detail karena A3 tidak ada di tabel conditional template):** A3 (Security Hardening) di `06a_CODE_MIGRATION_PHASES.md` fokus ke "semua model yang dirujuk view/action/relasi punya ACL valid", khususnya TransientModel (wizard). Modul ini: (1) tidak punya wizard/TransientModel sama sekali, (2) tidak punya model baru (`_name`) — seluruhnya `_inherit`, jadi tidak butuh ACL baru, (3) satu-satunya file ACL yang ada (`security/ir.model.access.csv`) sudah dead/menganggur dari 17.0 (F-07/`[BSL-015]`, entrinya di-comment di manifest) dan **dipertahankan apa adanya** sesuai baseline — tidak diaktifkan, tidak dihapus.

## [Fase A4] Skeleton & Folder Integrity

- **Scope:** struktur folder `advanced_sales_analysis/` (models/, controllers/, security/, static/, tests/) + `__init__.py`
- **Aksi:** Diverifikasi (bukan diubah) — struktur folder dan `__init__.py` konsisten, tidak ada folder yang hilang/rusak. Tidak ada aksi perbaikan diperlukan.
- **Secara eksplisit TIDAK dilakukan:** Tidak ada perubahan business logic/XML/security/dependency.
- **Risiko:** LOW
- **Status:** ✅ Selesai (sanity-check, tidak ada perubahan)

## [Fase A5] Python API Compatibility (Models Only)

- **Scope:** `models/sale_report.py` (satu-satunya file Python model)
- **Item spec (ref):** `03_spec/03_MIGRATION_SPEC.md` §2 (semua baris "Tidak berubah"), `02_diff/02_DIFF_ANALYSIS.md` DIFF-01 s/d DIFF-05
- **Aksi:** Diverifikasi (bukan diubah) — tidak ada override `create()`/`copy()`/`_name_search()`/`_check_recursion()`/`search()` (selain pemanggilan `search()` biasa, bukan override) di modul ini yang terkena perubahan API 17→18 yang dicatat `knowledge/version-diffs/17-to-18.md`. Tidak ada `user_has_groups`, tidak ada `fields.function`, tidak ada `group_operator`/`aggregator` di field milik modul sendiri (dikonfirmasi Step 2 DIFF-05). Tidak ada perubahan kode diperlukan.
- **Secara eksplisit TIDAK dilakukan:** Tidak ada rewrite/refactor apa pun ke `models/sale_report.py` — file ini identik byte-per-byte dengan `source-codebase` (kecuali `__manifest__.py` yang disentuh di A1).
- **Risiko:** LOW (dikonfirmasi analisis Step 2, bukan diasumsikan)
- **Status:** ✅ Selesai (tidak ada perubahan kode)

## [Fase B1] Model Risiko Rendah

- **Scope:** `models/sale_report.py` — `sale.report`, `account.move`, `sale.order.line` (`_inherit`, tidak ada model kompleks/JSON/dynamic — makanya B2 N/A)
- **Item spec (ref):** `03_spec/03_MIGRATION_SPEC.md` §2b "Kompatibilitas Data Model" #1 (DIFF-06, `@api.depends` melingkar)
- **Aksi:** Diverifikasi kelengkapan `@api.depends` per compute field — dikonfirmasi identik dengan `source-codebase` (tidak ada penambahan/pengurangan dependency). Satu item ditandai butuh re-verifikasi EKSEKUSI (bukan analisis statis) di Step 9: `@api.depends` melingkar antara `amount_to_invoice`/`waiting_for_payment`/`amount_received` di `sale.order.line` — tidak diubah/"diperbaiki" di sini (itu di luar scope migrasi identik, `01a_MIGRATION_INTAKE.md` §5).
- **Secara eksplisit TIDAK dilakukan:** Tidak membersihkan `@api.depends` melingkar meski secara teknis "kode yang menyesatkan" (`[BSL-021]`) — dipertahankan sesuai prinsip source-of-truth migrasi.
- **Risiko:** LOW (dampak tidak terbukti di eksekusi 17.0; status di 18.0 masih "belum pasti", dibawa ke Step 9)
- **Status:** ✅ Selesai (tidak ada perubahan kode; item verifikasi dibawa ke Step 9 secara eksplisit)

## [Fase G2] Validasi Akhir (Runtime)

- **Scope:** Diff/fix breaking dari Step 2/3 yang relevan — DIFF-02 (kolisi `amount_paid`), dan MF-01 (granularitas `sale.report`, ditemukan di G1 percobaan #1-2, lihat `FINDINGS.md`)
- **Aksi:** Kriteria minimal G2 (server start tanpa warning fatal, tidak ada error console browser di halaman terkait diff/fix, diff/fix breaking terkonfirmasi valid di runtime) **sudah terpenuhi lewat G1 percobaan #3** — tidak perlu sesi browser terpisah:
  - Server start: tidak ada warning fatal (hanya WARNING label field duplikat yang sudah diketahui/F-13, dan WARNING zombie chrome_crashpad yang benign/normal saat teardown test headless).
  - `test_qa_measures_baru_tersedia_di_pivot_sales_analysis` (`tests/test_qa_browser.py`) menjalankan Chrome headless ASLI (bukan simulasi) — navigasi ke Sales Analysis, cek measure baru muncul di pivot UI, hasil "test successful" di log. Ini smoke-check runtime yang genuinely membuka halaman terkait diff (`[BSL-005]`).
  - MF-01 (granularitas `sale.report` 18.0) terkonfirmasi valid di runtime lewat `test_ac_07_03_group_by_granularitas_18_0` — bukan cuma analisis statis.
- **Secara eksplisit TIDAK dilakukan:** Tidak ada sweep AC penuh di G2 (itu tugas Step 9/10) — scope G2 sempit sesuai `06a_CODE_MIGRATION_PHASES.md`.
- **Risiko:** LOW
- **Status:** ✅ Selesai

## [Fase A5 — amandemen retroaktif] Rename field MF-02 (dipicu Step 8 Code Review)

> Entri A5 di atas (2026-08-21, sebelum Step 8) menyatakan "tidak ada perubahan diperlukan" — ternyata tidak lengkap. Step 8 checklist wajib "cek tabrakan nama method dengan core" menemukan kolisi yang terlewat di Step 2/6. Dicatat sebagai entri baru (append-only), bukan mengedit entri lama.

- **Scope:** `advanced_sales_analysis/models/sale_report.py` (class `SaleOrderLine`), `tests/test_sale_order_line.py`, `tests/test_account_move.py`
- **Item spec (ref):** `FINDINGS.md` MF-02, `08_review/08_CODE_REVIEW.md` CR-01
- **Aksi:**
  - `models/sale_report.py:90`: field `amount_to_invoice` → `asa_amount_to_invoice` (tetap `Float`, `store=True`, label "Amount Received" TIDAK diubah — F-13 dipertahankan)
  - `models/sale_report.py:94`: method `_compute_amount_to_invoice` → `_compute_asa_amount_to_invoice`
  - `models/sale_report.py:143`: assignment `line.amount_to_invoice` → `line.asa_amount_to_invoice`
  - `models/sale_report.py:145,194`: string `'amount_to_invoice'` di 2 `@api.depends()` → `'asa_amount_to_invoice'`
  - `models/sale_report.py:17`: SQL `SUM(l.amount_to_invoice)` → `SUM(l.asa_amount_to_invoice)` di dalam `_select_additional_fields()` (dict key `'amount_to_invoice'` di sisi kiri TIDAK berubah — itu field `sale.report`, terpisah, tidak collide)
  - Test: semua rujukan `line.amount_to_invoice`/`order.order_line.amount_to_invoice`/`sol_fields['amount_to_invoice']` diperbarui ke `asa_amount_to_invoice`
- **Secara eksplisit TIDAK dilakukan:** Tidak mengubah semantik/formula perhitungan — HANYA nama field/method. `sale.report.amount_to_invoice` (field level laporan) TIDAK disentuh. Tidak memperbaiki label salah F-13 (masih "Amount Received", bug lama dipertahankan).
- **Catatan proses:** Edit ke `models/` awalnya BLOCKED oleh `.claude/settings.json` deny rule — AI tidak diizinkan melonggarkan permission sendiri (diblokir classifier level lebih tinggi) walau diminta eksplisit oleh user di chat. User melonggarkan deny rule secara manual sebelum AI melanjutkan edit.
- **Risiko:** LOW (rename mekanis, diverifikasi eksekusi — lihat Riwayat G1 #4)
- **Status:** ✅ Selesai

## [Fase B2] N/A — dikonfirmasi Applicability Check
## [Fase C1] N/A — tidak ada view sama sekali (lihat catatan Applicability Check di atas — kasus tepi, template standar mengasumsikan C1 selalu relevan)
## [Fase C2] N/A — dikonfirmasi Applicability Check
## [Fase D1] N/A — dikonfirmasi Applicability Check
## [Fase D2] N/A — dikonfirmasi Applicability Check
## [Fase E] N/A — dikonfirmasi Applicability Check
## [Fase F] N/A — dikonfirmasi Applicability Check (otomatis N/A karena E N/A)

---

## Temuan di Luar Spec

- [x] Ada — **MF-01** (granularitas `sale.report` berubah karena core 18.0, ditemukan saat G1). Ditangani sesuai prosedur: STOP, eskalasi ke user (bukan diputuskan sepihak), user memilih Opsi 1 (2026-08-21). Dokumen yang diupdate sebagai konsekuensi (bukan balik penuh ke Step 3/4 karena tidak ada perubahan STRATEGI migrasi, cuma koreksi kedalaman analisis Step 2 + acceptance criteria): `02_diff/02_DIFF_ANALYSIS.md` (DIFF-01, koreksi), `01_intake/01a_MIGRATION_INTAKE.md` §5, `01_intake/01b_BASELINE_SPEC.md` `[BSL-023]`, `05_acceptance/05a_MIGRATION_ACCEPTANCE_CRITERIA.md`/`05b` AC-07-03, `FINDINGS.md` MF-01, dan `advanced_sales_analysis/tests/test_sale_report.py` (test disesuaikan ke baseline 18.0 yang benar).

## Kontribusi ke Knowledge Base

- [x] Ada — dicatat ke `migration-records/advanced_sales_analysis_17.0_18.0/SUMMARY.md`:
  - **CAND-04** (baru): `06a_CODE_MIGRATION_PHASES.md` §Applicability Check standar tidak punya baris untuk Fase C1, dengan asumsi implisit "semua modul punya minimal satu view" — modul tanpa view sama sekali (`'data': []`) adalah kasus tepi yang tidak tercakup tabel conditional template. Kandidat: tambah C1 ke tabel Applicability Check (kondisional terhadap "modul punya `views/` folder?"), bukan diasumsikan selalu relevan.
