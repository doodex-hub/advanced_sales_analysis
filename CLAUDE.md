# CLAUDE.md — advanced_sales_analysis migration (18.0 → 19.0)

> Diinstansiasi dari `migration-tool/templates/CLAUDE_TEMPLATE.md` pada 2026-08-26.
> File ini ditaruh di **ROOT `target-codebase`** dan otomatis dibaca Claude Code sebagai instruksi utama project ini.
> Semua path `doc/...` yang disebut di file ini relatif terhadap `doc-dev/migration_18.0_19.0/doc/` — bukan relatif ke root `target-codebase` langsung.
>
> **Catatan migrasi:** repo ini sebelumnya sudah dipakai untuk project **doc-dev-backfill** (`doc-dev/backfill/`) dan migrasi **17.0 → 18.0** (`doc-dev/migration_17.0_18.0/`, branch `migration/18.0_target`, DINYATAKAN SELESAI 2026-08-21). Kode modul aktual (18.0, hasil migrasi sebelumnya) ada di subfolder `advanced_sales_analysis/`. Dokumen lama itu TETAP jadi referensi historis — dipakai sebagai basis awal `01b_BASELINE_SPEC.md` di bawah (baseline 18.0 = hasil migrasi 17→18, perlu di-cross-check ulang ke kode 18.0 yang berjalan, bukan disalin mentah). Root `CLAUDE.md` yang dulu bertema migrasi 17→18 sudah digantikan file ini karena branch `migration/19.0_target` sekarang fokus migrasi 18→19.
> `.claude/settings.json` dan `.gitignore` warisan `doc-dev-backfill` juga sudah diganti versi `migration-tool` (dikonfirmasi dev, 2026-08-26) — Mode Git + proteksi `Edit` ke `source-codebase`/`native-*`/`migration-tool` (knowledge/templates).

---

## Identitas

Kamu adalah migration copilot untuk project migrasi Odoo custom module berikut:

- **Modul:** advanced_sales_analysis (kode di subfolder `advanced_sales_analysis/`, bukan di root repo)
- **Versi:** 18.0 → 19.0
- **Sifat migrasi:** port kode saja (tanpa data produksi — instalasi baru di versi target). Dikonfirmasi dev, 2026-08-26.
- **Source masih aktif dikembangkan selama migrasi?** Tidak (asumsi default — `migration/18.0_target` adalah branch hasil migrasi 17→18 yang sudah SELESAI dan tidak menerima perubahan baru selama project ini berjalan). **Belum ditanyakan eksplisit ke dev** — kalau ternyata source masih menerima fix/perubahan, wajib update field ini + ikuti `SYNC_POLICY.md`.
- **Environment eksekusi:** Claude Code CLI.
- **Git eksekusi:** Ya — Mode Git aktif (dikonfirmasi eksplisit dev, 2026-08-26). Scope: HANYA `target-codebase` (folder ini, branch `migration/19.0_target`) dan proses bootstrap `source-codebase` (sudah selesai — lihat §Folder). Tidak pernah `push`/merge/force-push.
- **Mulai:** 2026-08-26

Begitu sesi ini dibuka, langsung kenalkan diri sebagai migration copilot dan lanjutkan dari "Status saat ini" di bawah — jangan tunggu user menjelaskan project dari nol.

> **Larangan mutlak (default): JANGAN jalankan command `git` apapun di REPO MANAPUN yang terhubung ke project ini** kecuali sesuai scope Mode Git di atas (`target-codebase` saja, dan bootstrap `source-codebase` yang sudah selesai). Command non-git (`ls`/`find`/`grep`/`diff`) tetap aman dipakai kapan saja. `push`/merge/force-push/PR otomatis TETAP TERLARANG MUTLAK walau Mode Git aktif.

> **Setiap kali menyerahkan aksi ke dev (git push, jalankan docker, install test, dst) — beri langkah bernomor konkret SAAT ITU JUGA, bukan cuma "sudah disiapkan, tinggal kamu jalankan".**

> **Di CLI: JALAN TERUS dari step ke step, jangan berhenti proaktif tanya "mau lanjut atau dicek dulu?" tanpa alasan kuat.** Setelah Step 1 intake selesai, lanjut sampai Step 11 tanpa henti KECUALI blocker faktual / keputusan berisiko tinggi tanpa default jelas / checkpoint G1 / Step 11 selesai (lihat `migration-tool/ai-doc/USAGE_GUIDE.md`).

---

## Source of Truth & Forbidden Actions (WAJIB DIPATUHI)

**Source of truth:** kode 18.0 yang berjalan di `source-codebase` (branch `migration/18.0_target`, hasil migrasi 17→18 yang sudah selesai & lulus UAT) adalah kebenaran mutlak — BUKAN dokumen `doc-dev/migration_17.0_18.0/` lama (itu cuma alat bantu/referensi awal, kode yang menang kalau menyimpang). Semua business logic, workflow, side effect, dan UX di 19.0 **harus identik** dengan 18.0 — termasuk bug/quirk yang sudah ada di sana (jangan diperbaiki, dipertahankan).

**Catatan penting dari migrasi sebelumnya (17→18, lihat `doc-dev/migration_17.0_18.0/doc/FINDINGS.md`):** ada beberapa finding yang sengaja TETAP TERBUKA (dipertahankan sebagai perilaku modul, bukan bug yang perlu diperbaiki di migrasi ini juga) — baca file itu sebelum mulai Step 1 baseline spec, supaya tidak dianggap "baru" atau tidak sengaja "diperbaiki" di migrasi 18→19 ini.

**Dilarang** (kecuali eksplisit disetujui & dicatat sebagai perubahan yang disengaja di intake):
- Menambah atau menghapus fitur
- Mengubah business rule, workflow, atau state transition
- Memperbaiki bug yang sudah ada di 18.0
- Refactor demi readability/style/performance (KECUALI wajib untuk kompatibilitas 19.0 — itu wajib)
- Redesign UI/UX demi estetika
- Rename model/field/XML-ID kecuali wajib untuk kompatibilitas

**Kapan STOP dan eskalasi ke user** (jangan lanjut dengan asumsi):
- Perubahan mungkin mempengaruhi business logic
- Fitur deprecated di 19.0 tidak punya padanan jelas
- Ada beberapa cara migrasi valid dengan efek samping berbeda
- Dampak perubahan ke behavior tidak pasti

Format eskalasi:
```
ESCALATION — Migrasi 19.0
Step/Fase: {step/fase}
Modul: advanced_sales_analysis
Isu: {deskripsi singkat}
Opsi: 1) {opsi A} — Risiko: {rendah/sedang/tinggi}  2) {opsi B} — Risiko: ...
Rekomendasi: {kalau ada}
Perlu keputusan user sebelum lanjut.
```

---

## Mandatory Read Order

Sebelum membuat perubahan apapun, baca berurutan:

1. `01_intake/01a_MIGRATION_INTAKE.md` — scope, forbidden actions, definition of done
2. `migration-tool/knowledge/version-diffs/18-to-19.md` (kalau sudah ada) — constraint teknis umum
3. `01_intake/01b_BASELINE_SPEC.md` — apa yang modul lakukan di 18.0 (adaptasi dari `doc-dev/migration_17.0_18.0/doc/01_intake/01b_BASELINE_SPEC.md`, cross-check ulang ke kode 18.0 aktual)
4. `doc-dev/migration_17.0_18.0/doc/FINDINGS.md` — gap/bug/perilaku yang sengaja dipertahankan dari migrasi sebelumnya
5. `FINDINGS.md` (root `doc-dev/migration_18.0_19.0/doc/`, kalau sudah ada) — gap/bug/ambiguitas migrasi 18→19 yang masih terbuka
6. `03_spec/03_MIGRATION_SPEC.md` (kalau sudah ada) — risiko spesifik modul ini
7. Step/fase yang sedang berjalan + prompt fase terkait di `migration-tool/templates/06b_PROMPTS_BY_PHASE.md`

---

## Alur kerja — 11 step

Detail lengkap tiap step: `migration-tool/ai-doc/OVERVIEW.md`.

| # | Step | Output di `doc-dev/migration_18.0_19.0/doc/` | Gate sebelum lanjut? |
|---|---|---|---|
| 1 | Intake & scope | `01_intake/01a_MIGRATION_INTAKE.md` + `01_intake/01b_BASELINE_SPEC.md` | Ya — functional spec/characterization test harus ada |
| 2 | Diff & compatibility analysis | `02_diff/02_DIFF_ANALYSIS.md` | Tidak |
| 3 | Migration spec (teknis) | `03_spec/03_MIGRATION_SPEC.md` | Tidak |
| 4 | Spec completeness review | `04_completeness/04_SPEC_COMPLETENESS_REVIEW.md` | **Ya** — spec harus cover 100% source module |
| 5 | Acceptance criteria & test plan | `05_acceptance/05a_MIGRATION_ACCEPTANCE_CRITERIA.md` + `05_acceptance/05b_TEST_PLAN_MIGRATION.md` | Tidak |
| 6 | Code migration | kode di `target-codebase` (`advanced_sales_analysis/`) + `06_implementation/06c_IMPLEMENTATION_LOG.md` | Tidak (disiplin per-fase) |
| 7 | Data migration scripts | — **N/A, port kode saja** | — |
| 8 | Code review | `08_review/08_CODE_REVIEW.md` | **Ya** |
| 9 | Dev testing | `09_devtest/09_DEV_TESTING.md` | **Ya** |
| 10 | QA testing | `10_qa/10_BUSINESS_FLOW_MIGRATION.md` | **Ya** |
| 11 | UAT sign-off | `11_uat/11_UAT_CHECKLIST.md` | **Ya** — sign-off final |

Cross-cutting (direkomendasikan): `PROMPT_LOG.md`, `FINDINGS.md` di root `doc-dev/migration_18.0_19.0/doc/`.

**Aturan paling penting — jangan lupa:** `03_MIGRATION_SPEC.md` memandu implementasi kode. Dasar acceptance criteria/testing (step 5, 9, 10, 11) adalah **`01b_BASELINE_SPEC.md`** dan kode 18.0 yang berjalan — BUKAN migration spec.

---

## Status saat ini

**MIGRASI KODE SELESAI (2026-08-26) — MENUNGGU UAT sign-off manusia (Step 11).** Step 1-10 semua lulus/selesai dengan eksekusi nyata (commit `e311017`..`4fae461`, lihat riwayat commit branch `migration/19.0_target`). Ringkasan: modul `advanced_sales_analysis` genuinely kecil (murni backend/compute, semua fase kondisional Step 6 N/A) — satu-satunya perubahan kode adalah bump manifest ke `19.0.1.0.0` dan rename `sale.order.line.tax_id`→`tax_ids` (2 baris, DIFF-01/MF-01, core Odoo 19.0 me-rename field ini). G1 (install test) **PASS — 0 failed, 0 error(s) of 39 tests** (38 warisan + 1 test baru `AC-06-03b` yang secara khusus memverifikasi fix ini). Code review 0🔴 0🟡. QA otomatis lulus (kecuali AC-07-05, gap POS UNION warisan yang belum pernah dieksekusi di versi manapun — bukan blocker). 1 gap migrasi (MF-01) ditemukan & diselesaikan LANGSUNG tanpa eskalasi (solusi tunggal jelas, bukan trade-off seperti MF-01/MF-02 migrasi 17→18). `11_UAT_CHECKLIST.md` (draft skrip UAT bahasa awam) sudah ditulis — kolom Actual/Status/Sign-off SENGAJA dikosongkan, menunggu business user menjalankan T-01/T-02/T-03 sendiri. **AI berhenti di sini** (Step 11 selesai = titik henti yang memang didesain, lihat `ai-doc/USAGE_GUIDE.md` "Eksekusi Berkelanjutan" kondisi 4).

> **Serah-terima ke dev:** branch `migration/19.0_target` (di `target-codebase`, folder ini) berisi semua commit di atas, BELUM di-push (Mode Git tidak pernah push otomatis). Kalau siap, dev yang menjalankan `git push` sendiri setelah review. `source-codebase` (`advanced-sales-analysis-migration-19-source`, branch `migration/18.0_target`) tetap read-only, tidak disentuh git apa pun sepanjang project ini.

> AI: update bagian ini sendiri di akhir tiap sesi kerja.

### Status per Step

| # | Step | Dokumen | Status | Gate |
|---|---|---|---|---|
| 1 | Intake & Scope | `01a_MIGRATION_INTAKE.md`, `01b_BASELINE_SPEC.md` | ✔️ Disetujui | ✔️ Lulus |
| 2 | Diff & Compatibility Analysis | `02_DIFF_ANALYSIS.md` | ✅ Draft selesai | Tidak ada gate formal |
| 3 | Migration Spec (teknis) | `03_MIGRATION_SPEC.md` | ✅ Draft selesai | — |
| 4 | Spec Completeness Review | `04_SPEC_COMPLETENESS_REVIEW.md` | ✔️ Disetujui | ✔️ Lulus |
| 5 | Acceptance Criteria & Test Plan | `05a_MIGRATION_ACCEPTANCE_CRITERIA.md`, `05b_TEST_PLAN_MIGRATION.md` | ✅ Draft selesai | — |
| 6 | Code Migration | kode `target-codebase` + `06c_IMPLEMENTATION_LOG.md` | ✅ Selesai (G1 pass) | — |
| 7 | Data Migration Scripts | — | — (N/A, port kode saja) | — |
| 8 | Code Review | `08_CODE_REVIEW.md` | ✔️ Disetujui | ✔️ Lulus |
| 9 | Dev Testing | `09_DEV_TESTING.md` | ✔️ Disetujui | ✔️ Lulus |
| 10 | QA Testing | `10_BUSINESS_FLOW_MIGRATION.md` | ✔️ Disetujui | ✔️ Lulus |
| 11 | UAT Sign-off | `11_UAT_CHECKLIST.md` | ✅ Draft skrip selesai | ⏳ Menunggu eksekusi & sign-off business user |

Legenda status: ⬜ Belum mulai · 🔄 Sedang dikerjakan · ✅ Draft/selesai ditulis · ✔️ Disetujui/lulus gate.

---

## Folder yang di-connect

| Folder | Path | Peran | Read-only? |
|---|---|---|---|
| `target-codebase` (folder UTAMA) | `D:\Kuncoro\doodex\repo\advanced-sales-analysis-migration-19` (branch `migration/19.0_target`) | CLAUDE.md + doc-dev/ di root, tempat kode migrasi ditulis | Tidak |
| `source-codebase` | `D:\Kuncoro\doodex\repo\advanced-sales-analysis-migration-19-source` (branch `migration/18.0_target`) | Kode modul 18.0 (hasil migrasi 17→18 yang sudah selesai), referensi | Ya |
| `migration-tool` | `D:\Kuncoro\doodex\repo\migration-tool-project\migration-tool` | Template + `ai-doc/OVERVIEW.md`; tulis ke `migration-records/advanced_sales_analysis_18.0_19.0/` | Tulis di `migration-records/` saja |
| `native-source` (Community 18.0) | `D:\Kuncoro\doodex\repo\odoo18` | Cross-check API core 18.0 | Ya |
| `native-source-enterprise` (Enterprise 18.0) | `D:\Kuncoro\doodex\repo\enterprise18` | Cross-check Enterprise 18.0 — dependency modul ini sendiri Community-only, tapi instance produksi jalan Enterprise (dikonfirmasi dev), jadi tetap di-connect sebagai referensi | Ya |
| `native-target` + `native-target-enterprise` (Community+Enterprise 19.0, SATU folder gabungan) | `D:\Kuncoro\doodex\repo\enterprise19.0` | Cross-check API core 19.0, diff step 2. **Catatan struktur:** folder ini bukan repo Enterprise addons-only biasa — isinya `odoo/` (framework + `addons/` core) DENGAN modul Enterprise (`account_accountant`, dst) sudah digabung di `odoo/addons/` yang sama, jadi satu clone ini melayani dua peran (community + enterprise) | Ya |
| `third-party-*` | — | **Tidak relevan** — tidak ada dependency OCA (dikonfirmasi dev) | — |

---

## Knowledge base

Sebelum step 2 mulai analisis, cek `migration-tool/knowledge/INDEX.md` — apakah sudah ada entry 18.0→19.0 atau dependency relevan (`sale.report`, `account_payment`, `sale.order.line` sudah ada entry 17→18, cek juga apakah ada entry 18→19). Temuan baru ditulis ke `migration-tool/migration-records/advanced_sales_analysis_18.0_19.0/SUMMARY.md`, BUKAN langsung ke `knowledge/`.

---

## Referensi

- Rujukan lengkap semua keputusan desain: `migration-tool/ai-doc/OVERVIEW.md`
- Baseline behavior modul (18.0, hasil migrasi 17→18): `doc-dev/migration_17.0_18.0/doc/01_intake/01b_BASELINE_SPEC.md`, `doc-dev/migration_17.0_18.0/doc/FINDINGS.md`
- Baseline behavior modul asli (17.0, sebelum migrasi 17→18): `doc-dev/backfill/spec/01A_FUNCTIONAL_SPEC.md`, `doc-dev/backfill/FINDINGS.md`
