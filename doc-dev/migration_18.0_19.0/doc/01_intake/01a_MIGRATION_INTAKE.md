# Migration Intake — advanced_sales_analysis

**Step:** 1 — Intake & Scope
**Versi:** 18.0 → 19.0
**Tanggal:** 2026-08-26
**Status:** ✔️ Disetujui (gate lulus, tidak ada koreksi user terhadap ringkasan §Ringkasan)

---

## 0. Folder Referensi

Dikonfirmasi eksplisit dev (2026-08-26):

- [x] `native-target` (Community, checkout 19.0) — **digabung dengan Enterprise di satu folder**, lihat catatan struktur di bawah. Path: `D:\Kuncoro\doodex\repo\enterprise19.0`
- [x] `native-source` (Community, checkout 18.0) — Path: `D:\Kuncoro\doodex\repo\odoo18`
- [x] `native-target-enterprise` — dev awalnya bertanya "apa ini? core odoo 19 jadi satu di enterprise-19.0" — dikonfirmasi lewat inspeksi langsung (`ls`): folder `enterprise19.0` **bukan** repo Enterprise addons-only standar (yang isinya cuma daftar folder addon, seperti `enterprise18`), melainkan struktur repo Odoo lengkap (`odoo/`, `odoo.egg-info`, `setup.py`, dst) DENGAN modul Enterprise (`account_accountant`, `account_asset`, dst) sudah tergabung di `odoo/addons/` yang sama dengan modul Community (`account`, dst). Jadi satu folder ini melayani DUA peran (`native-target` DAN `native-target-enterprise`) sekaligus. Path: `D:\Kuncoro\doodex\repo\enterprise19.0` (sama seperti di atas)
- [x] `native-source-enterprise` — Path: `D:\Kuncoro\doodex\repo\enterprise18` (struktur standar, addons-only, terpisah dari `odoo18`)
- [x] `third-party-source`/`third-party-target` — dikonfirmasi TIDAK ADA dependency OCA/vendor (lihat §0a-Enterprise di bawah)

### 0a. Konfirmasi Branch/Versi

- [x] `source-codebase` — Path: `D:\Kuncoro\doodex\repo\advanced-sales-analysis-migration-19-source`, branch `migration/18.0_target` (dibuat via clone sibling dari branch remote yang sama, per keputusan dev). Ini adalah branch hasil migrasi 17.0→18.0 yang **sudah dinyatakan SELESAI dan lulus UAT** (2026-08-21).
- [x] `target-codebase` — Path: `D:\Kuncoro\doodex\repo\advanced-sales-analysis-migration-19` (folder ini), branch BARU `migration/19.0_target`, dibuat dari `origin/migration/18.0_target` (dikonfirmasi dev, bukan tebakan AI).
- [x] Dikonfirmasi dev: kedua folder adalah clone fisik terpisah (bukan symlink/alias).
- [x] Versi semantik dikonfirmasi eksplisit dev: **18.0 → 19.0**.

### 0b. Gate: Path Absolut di `.claude/settings.json`

- [x] `ABS_PATH_SOURCE_CODEBASE` → `D:/Kuncoro/doodex/repo/advanced-sales-analysis-migration-19-source`
- [x] `ABS_PATH_MIGRATION_TOOL` → `D:/Kuncoro/doodex/repo/migration-tool-project/migration-tool`
- [x] `ABS_PATH_NATIVE_SOURCE` → `D:/Kuncoro/doodex/repo/odoo18`
- [x] `ABS_PATH_NATIVE_SOURCE_ENTERPRISE` → `D:/Kuncoro/doodex/repo/enterprise18`
- [x] `ABS_PATH_NATIVE_TARGET` + `ABS_PATH_NATIVE_TARGET_ENTERPRISE` → keduanya `D:/Kuncoro/doodex/repo/enterprise19.0` (folder gabungan, lihat §0)
- [x] `ABS_PATH_THIRD_PARTY_SOURCE`/`ABS_PATH_THIRD_PARTY_TARGET` → baris deny dihapus (tidak dipakai)
- Sudah diterapkan ke `.claude/settings.json` dan di-commit (`3131a53`, "Bootstrap migration 18.0 to 19.0...").

---

## Ringkasan untuk Review — Perlu Konfirmasi User

1. **Sifat modul Enterprise:** modul `advanced_sales_analysis` sendiri **tidak** depend ke Enterprise/OCA apa pun di manifest maupun kode (cross-check kode: tidak ada referensi model Enterprise) — TAPI instance produksi dev berjalan Odoo Enterprise, jadi `native-*-enterprise` tetap di-connect sebagai referensi kalau `sale.report`/`account.move` ternyata di-extend modul Enterprise lain (relevan untuk MRO/kolisi field, lihat lesson MF-02 migrasi sebelumnya). **Dikonfirmasi dev — tidak perlu ditanya ulang.**
2. **Source (`migration/18.0_target`) dianggap dibekukan** selama project 18→19 ini berjalan (§4b) — **asumsi AI, belum ditanyakan eksplisit ke dev.** Berisiko rendah (branch source sudah lulus UAT & tidak ada indikasi pekerjaan lanjutan di sana), tapi kalau ternyata ada fix susulan yang harus disinkronkan, beri tahu AI supaya `SYNC_POLICY.md` diaktifkan.
3. **`.claude/settings.json`/`.gitignore` warisan `doc-dev-backfill`** (permission docker-env/tests/tours, hook `backfill-command-log.jsonl`) sudah **diganti total** dengan versi `migration-tool` (Mode Git + deny `ABS_PATH_*`), sesuai keputusan eksplisit dev — bukan digabung. Kalau ternyata ada command spesifik dari config lama yang masih dibutuhkan (mis. edit langsung ke `docker-env/`, `tests/`, `static/tests/tours/` tanpa lewat allow list umum `Edit(**)` yang sekarang ada), beri tahu supaya ditambahkan kembali.
4. Tidak ada ambiguitas lain yang genuinely butuh keputusan manusia di Step 1 ini — sisanya straightforward (module sudah 100% terdokumentasi dari migrasi 17→18 sebelumnya).

---

## 1. Modul & Scope

- Modul yang dimigrasi: **advanced_sales_analysis** (satu modul, kode di subfolder `advanced_sales_analysis/`)
- Deskripsi singkat fungsi modul: memperkaya laporan Sales Analysis (`sale.report`) dengan 3 metrik finansial (Amount Received, Waiting for Payment, Amount To Invoice) berbasis status pembayaran invoice dan penanganan uang muka. Detail lengkap: `01b_BASELINE_SPEC.md`.
- Modul-modul saling depend: tidak ada modul lain dalam scope migrasi ini (single-module project).

## 2. Dependency Map (auto-scan)

| Dependency | Tipe | Versi tersedia di target (19.0)? | Catatan |
|---|---|---|---|
| `base` | Native Community | Ya | Standar core |
| `sale` | Native Community | Ya | Perlu diff detail Step 2 — `sale.report._select_additional_fields()`/`_group_by_sale()`, `sale.order.line` field baru |
| `account` | Native Community | Ya | Perlu diff detail Step 2 — `account.move` hook, kolisi nama field historis (`account_payment`, lihat BSL-006) |
| `sale_management` | Native Community | Ya | Belum ada indikasi override spesifik dari modul ini |

Dependency opsional yang dicek runtime (tidak selalu terlihat di manifest):

- `account_payment` (`auto_install: ['account']`, Native Community) — **selalu aktif** bareng `account`, berkolisi nama field+method (`amount_paid`/`_compute_amount_paid`) dengan modul ini sejak 17.0 (`[BSL-006]`, dipertahankan sebagai behavior yang harus identik, BUKAN target perbaikan migrasi ini). **Wajib dicek ulang di Step 2** apakah definisi core berubah di 19.0.
- `point_of_sale` (Native Community, kalau terinstall) — berbagi hook `_select_additional_fields()` lewat `_select_pos()` miliknya sendiri. Perlu dicek Step 2 apakah kontrak hook ini masih kompatibel di 19.0.

## 2b. Struktur & Fitur Modul (auto-scan)

| Fitur | Ada di modul? | Lokasi/bukti | Fase step 6 relevan |
|---|---|---|---|
| Controllers (route custom) | Tidak | `controllers/controllers.py` kosong (2 baris komentar), tetap di-import | D1 → N/A |
| Assets/CSS/JS custom | Tidak | Tidak ada `static/src/`, tidak ada key `assets` di manifest | D2, E, F → N/A |
| Komponen Owl/JavaScript custom | Tidak | Tidak ada file `.js` | E, F → N/A |
| Field JSON, relasi berantai, dynamic model creation | Tidak | Semua field `Float` sederhana, tidak ada `self.env[var]` | B2 → N/A |
| View pakai `attrs=`/`states=`/`domain=`/`context=` dinamis | Tidak | `'data': []` — tidak ada view/XML sama sekali | C1, C2 → N/A |

Semua fase kondisional (B2, C1, C2, D1, D2, E, F) **N/A** — modul ini murni backend/compute + SQL view lewat `_select_additional_fields()` (identik dengan kesimpulan migrasi 17→18 sebelumnya). Step 6 fokus di Fase A (install/compat) dan B1 (model/field inti).

## 3. Sifat Migrasi

- [x] Port kode saja (belum ada data produksi — instalasi baru di versi target). Dikonfirmasi eksplisit dev, 2026-08-26.
- [ ] Upgrade instance (ada data produksi)

## 4. Baseline Spec / Characterization Test (gate)

- [x] Cek `FUNCTIONAL_SPEC.md` lama: tidak ada file bernama itu langsung, tapi ada rangkaian dokumen setara —
  1. `doc-dev/backfill/spec/01A_FUNCTIONAL_SPEC.md` + `doc-dev/backfill/FINDINGS.md` (baseline 17.0, execution-verified 38 test, proyek doc-dev-backfill terpisah)
  2. `doc-dev/migration_17.0_18.0/doc/01_intake/01b_BASELINE_SPEC.md` (baseline 17.0 direkonsiliasi ke skema `BSL-NNN`, cross-checked ke kode 17.0)
  3. `doc-dev/migration_17.0_18.0/doc/FINDINGS.md` (2 gap migrasi 17→18, MF-01/MF-02, KEDUANYA sudah RESOLVED dan jadi bagian baseline 18.0 — lihat §8 di bawah)
  - Proses pengisian `01b_BASELINE_SPEC.md` (18.0→19.0) ini: (1) baca ketiga dokumen di atas sebagai draft, (2) cross-check tiap klaim langsung ke kode 18.0 aktual (`advanced_sales_analysis/models/sale_report.py` di `source-codebase`/`target-codebase` — identik saat ini, baru di-branch), (3) SEMUA klaim cocok 100% — tidak ditemukan penyimpangan baru, lihat `01b_BASELINE_SPEC.md`.
- [x] `01b_BASELINE_SPEC.md` sudah diisi.

### 4a. Dokumen Pelengkap Lain

- [x] Tidak ada dokumen pelengkap lain di luar yang sudah disebut §4 di atas — modul ini sudah didokumentasikan penuh lewat 2 project sebelumnya (`doc-dev-backfill`, migrasi 17→18). Tidak ditanyakan ulang ke dev secara terpisah karena riwayat dokumen sudah lengkap dan dev sudah mengonfirmasi jalur baca (§0 percakapan intake).

## 4b. Source Masih Aktif Dikembangkan?

- [x] Tidak — `migration/18.0_target` adalah deliverable migrasi 17→18 yang sudah lulus UAT (2026-08-21), dibekukan sebagai source project ini. **Asumsi AI berisiko rendah, belum ditanyakan eksplisit** (lihat §Ringkasan poin 2) — kalau salah, `SYNC_POLICY.md` perlu diaktifkan.

## 5. Scope Boundary

- Yang harus tetap identik pasca migrasi: semua business logic yang didokumentasikan di `01b_BASELINE_SPEC.md` (3 metrik `sale.report`, 8 field `account.move`, logic uang muka via string `"Down payment"`, semua quirk `[BSL-013]`..`[BSL-022]`) — termasuk field `asa_amount_to_invoice` (nama hasil rename MF-02, BUKAN `amount_to_invoice` — perubahan nama itu sendiri sudah final, bukan sesuatu yang di-revert).
- Yang sengaja diubah/di-drop dari 17.0 (diwarisi sebagai baseline 18.0, BUKAN keputusan baru migrasi ini):
  - Granularitas `sale.report` GROUP BY mengikuti kolom core 18.0 (`price_unit`, `invoice_status`, `is_downpayment` ditambah core, `analytic_account_id` dihapus core) — MF-01, disetujui pemilik modul 2026-08-21.
  - Field `sale.order.line.amount_to_invoice` di-rename `asa_amount_to_invoice` untuk menghindari kolisi dengan field core baru 18.0 — MF-02, disetujui pemilik modul 2026-08-21.
- Belum ada perubahan scope baru yang diusulkan khusus untuk migrasi 18→19 — kalau Step 2/6 menemukan gap serupa (core 19.0 menambah kolom/field baru yang collide), ikuti pola eskalasi `ESCALATION`/`FINDINGS.md` yang sama seperti MF-01/MF-02.

## 6. Constraint

- Deadline: belum disebutkan dev — tidak mendesak berdasarkan konteks percakapan.
- Owner tiap step: dev (Kuncoro) sebagai pemilik modul & pengambil keputusan eskalasi; AI (migration copilot) mengeksekusi 11 step.
