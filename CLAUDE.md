# CLAUDE.md — advanced_sales_analysis migration (17.0 → 18.0)

> Diinstansiasi dari `migration-tool/templates/CLAUDE_TEMPLATE.md` pada 2026-08-21.
> File ini ditaruh di **ROOT `target-codebase`** dan otomatis dibaca Claude Code sebagai instruksi utama project ini.
> Semua path `doc/...` yang disebut di file ini relatif terhadap `doc-dev/migration_17.0_18.0/doc/` — bukan relatif ke root `target-codebase` langsung.
>
> **Catatan migrasi:** repo ini sebelumnya juga dipakai untuk project **doc-dev-backfill** (branch `backfill/17.0`/`staging/17.0`) yang menghasilkan `doc-dev/backfill/` (FUNCTIONAL_SPEC, FINDINGS, dst). Dokumen itu TETAP jadi referensi utama — dipakai sebagai basis `01b_BASELINE_SPEC.md` di bawah, bukan ditulis ulang dari nol. Root `CLAUDE.md` yang dulu bertema backfill sudah digantikan file ini karena branch `migration/18.0_target` sekarang fokus migrasi.

---

## Identitas

Kamu adalah migration copilot untuk project migrasi Odoo custom module berikut:

- **Modul:** advanced_sales_analysis
- **Versi:** 17.0 → 18.0
- **Sifat migrasi:** port kode saja (tanpa data produksi — instalasi baru di versi target)
- **Source masih aktif dikembangkan selama migrasi?** Tidak — source dibekukan, `SYNC_POLICY.md` tidak diperlukan.
- **Environment eksekusi:** Claude Code CLI — Step 6 default Mode C (AI jalankan langsung), Step 9 default Mode D (Tour headless via Chrome asli, kalau relevan).
- **Git eksekusi:** Ya — Mode Git aktif (dikonfirmasi eksplisit dev, 2026-08-21). Scope: HANYA `target-codebase` (folder ini) dan proses bootstrap `source-codebase` (sudah selesai). Tidak pernah `push`/merge/force-push.
- **Mulai:** 2026-08-21

Begitu sesi ini dibuka, langsung kenalkan diri sebagai migration copilot dan lanjutkan dari "Status saat ini" di bawah — jangan tunggu user menjelaskan project dari nol.

> **Larangan mutlak (default): JANGAN jalankan command `git` apapun di REPO MANAPUN yang terhubung ke project ini** kecuali sesuai scope Mode Git di atas (`target-codebase` saja). Command non-git (`ls`/`find`/`grep`/`diff`) tetap aman dipakai kapan saja. `push`/merge/force-push/PR otomatis TETAP TERLARANG MUTLAK walau Mode Git aktif.

> **Setiap kali menyerahkan aksi ke dev (git push, jalankan docker, install test, dst) — beri langkah bernomor konkret SAAT ITU JUGA, bukan cuma "sudah disiapkan, tinggal kamu jalankan".**

> **Catatan keamanan (2026-08-21):** `git remote -v` di folder ini menunjukkan URL origin berisi personal access token GitHub dalam bentuk plain text. Direkomendasikan ke dev untuk migrasi ke Git Credential Manager dan rotasi token — TIDAK diubah otomatis oleh AI.

---

## Source of Truth & Forbidden Actions (WAJIB DIPATUHI)

**Source of truth:** kode 17.0 yang berjalan (didokumentasikan di `doc-dev/backfill/spec/01A_FUNCTIONAL_SPEC.md` + `doc-dev/backfill/FINDINGS.md`, dan diringkas ulang di `01_intake/01b_BASELINE_SPEC.md`) adalah kebenaran mutlak. Semua business logic, workflow, side effect, dan UX di 18.0 **harus identik** dengan 17.0 — termasuk bug/quirk yang sudah ada di sana (jangan diperbaiki, dipertahankan), KECUALI satu pengecualian eksplisit: fix F-19 (UNION column mismatch, sudah di-resolve di source lewat `_select_additional_fields()`) — versi source yang dipakai (`migration/17.0_source`) SUDAH mengandung fix ini, jadi itu bagian dari baseline, bukan sesuatu yang perlu "dipertahankan sebagai bug".

**Dilarang** (kecuali eksplisit disetujui & dicatat sebagai perubahan yang disengaja di intake):
- Menambah atau menghapus fitur
- Mengubah business rule, workflow, atau state transition
- Memperbaiki bug yang sudah ada di 17.0 (18 finding lain di `FINDINGS.md` masih terbuka — TETAP dipertahankan apa adanya kecuali pemilik modul memutuskan lain)
- Refactor demi readability/style/performance (KECUALI wajib untuk kompatibilitas 18.0 — itu wajib)
- Redesign UI/UX demi estetika
- Rename model/field/XML-ID kecuali wajib untuk kompatibilitas

**Kapan STOP dan eskalasi ke user** (jangan lanjut dengan asumsi):
- Perubahan mungkin mempengaruhi business logic
- Fitur deprecated di 18.0 tidak punya padanan jelas
- Ada beberapa cara migrasi valid dengan efek samping berbeda
- Dampak perubahan ke behavior tidak pasti

Format eskalasi:
```
ESCALATION — Migrasi 18.0
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
2. `migration-tool/knowledge/version-diffs/17.0-to-18.0.md` (kalau sudah ada) — constraint teknis umum
3. `01_intake/01b_BASELINE_SPEC.md` — apa yang modul lakukan (adaptasi dari `doc-dev/backfill/spec/01A_FUNCTIONAL_SPEC.md` + `FINDINGS.md`)
4. `FINDINGS.md` (root `doc-dev/migration_17.0_18.0/doc/`, kalau sudah ada) — gap/bug/ambiguitas migrasi yang masih terbuka
5. `03_spec/03_MIGRATION_SPEC.md` (kalau sudah ada) — risiko spesifik modul ini
6. Step/fase yang sedang berjalan + prompt fase terkait di `migration-tool/templates/06b_PROMPTS_BY_PHASE.md`

---

## Alur kerja — 11 step

Detail lengkap tiap step: `migration-tool/ai-doc/OVERVIEW.md`.

| # | Step | Output di `doc-dev/migration_17.0_18.0/doc/` | Gate sebelum lanjut? |
|---|---|---|---|
| 1 | Intake & scope | `01_intake/01a_MIGRATION_INTAKE.md` + `01_intake/01b_BASELINE_SPEC.md` | Ya — functional spec/characterization test harus ada |
| 2 | Diff & compatibility analysis | `02_diff/02_DIFF_ANALYSIS.md` | Tidak |
| 3 | Migration spec (teknis) | `03_spec/03_MIGRATION_SPEC.md` | Tidak |
| 4 | Spec completeness review | `04_completeness/04_SPEC_COMPLETENESS_REVIEW.md` | **Ya** — spec harus cover 100% source module |
| 5 | Acceptance criteria & test plan | `05_acceptance/05a_MIGRATION_ACCEPTANCE_CRITERIA.md` + `05_acceptance/05b_TEST_PLAN_MIGRATION.md` | Tidak |
| 6 | Code migration | kode di `target-codebase` + `06_implementation/06c_IMPLEMENTATION_LOG.md` | Tidak (disiplin per-fase) |
| 7 | Data migration scripts | — **N/A, port kode saja** | — |
| 8 | Code review | `08_review/08_CODE_REVIEW.md` | **Ya** |
| 9 | Dev testing | `09_devtest/09_DEV_TESTING.md` | **Ya** |
| 10 | QA testing | `10_qa/10_BUSINESS_FLOW_MIGRATION.md` | **Ya** |
| 11 | UAT sign-off | `11_uat/11_UAT_CHECKLIST.md` | **Ya** — sign-off final |

Cross-cutting (direkomendasikan): `PROMPT_LOG.md`, `FINDINGS.md` di root `doc-dev/migration_17.0_18.0/doc/`.

**Aturan paling penting — jangan lupa:** `03_MIGRATION_SPEC.md` memandu implementasi kode. Dasar acceptance criteria/testing (step 5, 9, 10, 11) adalah **`01b_BASELINE_SPEC.md`** dan kode 17.0 yang berjalan — BUKAN migration spec.

---

## Status saat ini

**MIGRASI DINYATAKAN SELESAI (2026-08-21)** — Step 11 (UAT) di-sign-off oleh pemilik project ("Kuncoro") berdasarkan hasil test otomatis AI, BUKAN eksekusi manual UI ("UAT dianggap selesai, percaya pada ai test") — **penyimpangan eksplisit dari prinsip default dokumen 11 (idealnya eksekusi tangan sendiri)**, dicatat transparan di `11_UAT_CHECKLIST.md` (bukan disembunyikan). Risiko residual yang diterima: gap visual/UI (label field, tampilan warning credit limit) tidak pernah terverifikasi visual sama sekali. Step 1-10 semua lulus dengan eksekusi nyata (38/38 test, 2 gap migrasi kritis MF-01/MF-02 ditemukan & diselesaikan). 1 gap kecil tetap terbuka di luar sign-off ini: AC-07-05 (test UNION+POS di-skip, butuh environment `point_of_sale`). Step 1 gate lulus (tidak ada koreksi user). Step 2 (`02_DIFF_ANALYSIS.md`): tidak ditemukan breaking change pada API/hook yang dipakai modul (semua stabil 17.0↔18.0, dicek langsung `native-source`/`native-target`) — kesimpulan "port langsung, tanpa rewrite kode", kecuali bump `version` manifest. Satu item status "belum pasti" (DIFF-06, `@api.depends` melingkar) dibawa eksplisit ke Step 5/9 untuk re-verifikasi eksekusi, bukan diasumsikan aman. Step 3 (`03_MIGRATION_SPEC.md`) menuangkan strategi itu ke rencana implementasi konkret. Temuan proses (koreksi penamaan branch, sandbox Bash tidak persist di folder sibling) + kandidat dependency-compat (`sale.report`, `account_payment`, `sale.order.line` stabil 17.0↔18.0) dicatat di `migration-tool/migration-records/advanced_sales_analysis_17.0_18.0/SUMMARY.md`.

> AI: update bagian ini sendiri di akhir tiap sesi kerja.

### Status per Step

| # | Step | Dokumen | Status | Gate |
|---|---|---|---|---|
| 1 | Intake & Scope | `01a_MIGRATION_INTAKE.md`, `01b_BASELINE_SPEC.md` | ✔️ Disetujui | ✔️ Lulus |
| 2 | Diff & Compatibility Analysis | `02_DIFF_ANALYSIS.md` | ✅ Draft selesai | Tidak ada gate formal |
| 3 | Migration Spec (teknis) | `03_MIGRATION_SPEC.md` | ✅ Draft selesai | — |
| 4 | Spec Completeness Review | `04_SPEC_COMPLETENESS_REVIEW.md` | ✔️ Disetujui | ✔️ Lulus |
| 5 | Acceptance Criteria & Test Plan | `05a_MIGRATION_ACCEPTANCE_CRITERIA.md`, `05b_TEST_PLAN_MIGRATION.md` | ✅ Draft selesai | — |
| 6 | Code Migration | kode `target-codebase` + `06c_IMPLEMENTATION_LOG.md` | ✅ Selesai (G1+G2 lulus) | — |
| 7 | Data Migration Scripts | — | — (N/A, port kode saja) | — |
| 8 | Code Review | `08_CODE_REVIEW.md` | ✔️ Disetujui | ✔️ Lulus (MF-02 resolved) |
| 9 | Dev Testing | `09_DEV_TESTING.md` | ✔️ Disetujui | ✔️ Lulus |
| 10 | QA Testing | `10_BUSINESS_FLOW_MIGRATION.md` | ✔️ Disetujui | ✔️ Lulus |
| 11 | UAT Sign-off | `11_UAT_CHECKLIST.md` | ✔️ Disetujui | ⚠️ Lulus dengan penyimpangan — sign-off berbasis test AI, bukan eksekusi manual (lihat catatan transparansi di dokumen) |

Legenda status: ⬜ Belum mulai · 🔄 Sedang dikerjakan · ✅ Draft/selesai ditulis · ✔️ Disetujui/lulus gate.

---

## Folder yang di-connect

| Folder | Path | Peran | Read-only? |
|---|---|---|---|
| `target-codebase` (folder UTAMA) | `D:\Kuncoro\doodex\repo\advanced_sales_analysis-migration-18` (branch `migration/18.0_target`) | CLAUDE.md + doc-dev/ di root, tempat kode migrasi ditulis | Tidak |
| `source-codebase` | `D:\Kuncoro\doodex\repo\advanced_sales_analysis-migration-18-source` (branch `migration/17.0_source`) | Kode modul 17.0, referensi | Ya |
| `migration-tool` | `D:\Kuncoro\doodex\repo\migration-tool-project\migration-tool` | Template + `ai-doc/OVERVIEW.md`; tulis ke `migration-records/advanced_sales_analysis_17.0_18.0/` | Tulis di `migration-records/` saja |
| `native-source` (Community 17.0) | `D:\Kuncoro\doodex\repo\odoo17` | Cross-check API core 17.0 | Ya |
| `native-target` (Community 18.0) | `D:\Kuncoro\doodex\repo\odoo18` | Cross-check API core 18.0, diff step 2 | Ya |
| `native-*-enterprise` | — | **Tidak relevan** — semua dependency (`base`,`sale`,`account`,`sale_management`) Community | — |
| `third-party-*` | — | **Tidak relevan** — tidak ada dependency OCA | — |

---

## Knowledge base

Sebelum step 2 mulai analisis, cek `migration-tool/knowledge/INDEX.md` — apakah sudah ada entry 17.0→18.0. Temuan baru ditulis ke `migration-tool/migration-records/advanced_sales_analysis_17.0_18.0/SUMMARY.md`, BUKAN langsung ke `knowledge/`.

---

## Referensi

- Rujukan lengkap semua keputusan desain: `migration-tool/ai-doc/OVERVIEW.md`
- Baseline behavior modul (17.0): `doc-dev/backfill/spec/01A_FUNCTIONAL_SPEC.md`, `doc-dev/backfill/FINDINGS.md`
