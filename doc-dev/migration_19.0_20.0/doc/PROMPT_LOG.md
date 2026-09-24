# Prompt Log — advanced_sales_analysis (19.0 → 20.0)

**Tujuan:** data empiris untuk `ai-doc/ROADMAP.md` Fase 5 (Otomasi Bertahap). Klasifikasi mengikuti `migration-tool/templates/PROMPT_LOG.md` (Normal / Tool-fix / Tidak dihitung).

---

## Log per Step

| Step | # Prompt Normal | # Prompt Tool-fix | Catatan |
|---|---|---|---|
| 0 — Bootstrap (sebelum step 1 resmi) | 0 | 0 | Conditioning dikerjakan di sesi terpisah (2026-09-24), tidak dihitung di sesi ini. |
| 1 — Intake & Baseline Spec | 2 | 0 | (1) Prompt pembuka "Lakukan migrasi 19=>20" + path tool/native/skills. (2) Jawaban dialog intake 4 pertanyaan (scope, aset store, POS UNION, eksekusi Docker/GUI git) — semua opsi rekomendasi dipilih. |
| 2 — Diff & Compatibility Analysis | 0 | 0 | |
| 3 — Migration Spec | 0 | 0 | |
| 4 — Spec Completeness Review | 0 | 0 | |
| 5 — Acceptance Criteria & Test Plan | 0 | 0 | |
| 6 — Code Migration (semua fase A-G2) | 0 | 0 | |
| 7 — Data Migration Scripts | 0 | 0 | N/A — port kode saja |
| 8 — Code Review | 0 | 0 | |
| 9 — Dev Testing | 0 | 0 | |
| 10 — QA Testing | 0 | 0 | |
| 11 — UAT Sign-off | 1 | 0 | "UAT sign-off pakai bukti test AI, tutup migrasinya" — sign-off berbasis bukti test AI (penyimpangan eksplisit) + penutupan migrasi. |
| **Total** | **3** | **0** | |

Step 2–10 berjalan tanpa prompt tambahan user (prinsip "Eksekusi Berkelanjutan"); satu-satunya titik henti adalah dialog intake Step 1.

## Catatan Definisi

Tidak ada revisi kriteria klasifikasi.
