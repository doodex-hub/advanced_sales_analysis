# Prompt Log — advanced_sales_analysis (18.0 → 19.0)

**Tujuan:** data empiris untuk `ai-doc/ROADMAP.md` Fase 5 (Otomasi Bertahap).

---

## Log per Step

| Step | # Prompt Normal | # Prompt Tool-fix | Catatan |
|---|---|---|---|
| 0 — Bootstrap (sebelum step 1 resmi) | 6 | 0 | Versi/sifat migrasi, source-codebase setup, Mode Git, nama branch, folder native-target/source (termasuk klarifikasi struktur gabungan Community+Enterprise `enterprise19.0`), konfirmasi Enterprise/OCA, GUI-client+working-tree pre-flight, pilihan config CLI (migration-tool vs warisan backfill). Semua project-instance decisions — TIDAK ada perubahan ke `migration-tool/templates`/`ai-doc` (jadi 0 Tool-fix), meski satu temuan proses (struktur `enterprise19.0` gabungan) dicatat sebagai KANDIDAT tool-fix di `migration-records/.../SUMMARY.md` — belum dieksekusi (butuh sesi curation terpisah). |
| 1 — Intake & Baseline Spec | 0 | 0 | Ditulis AI langsung dari hasil bootstrap + rekonsiliasi dokumen migrasi 17→18, tidak ada prompt tambahan user. |
| 2 — Diff & Compatibility Analysis | 0 | 0 | Ditulis AI langsung (delegasi riset ke agent internal), tidak ada prompt tambahan user. |
| 3 — Migration Spec | 0 | 0 | idem |
| 4 — Spec Completeness Review | 0 | 0 | idem |
| 5 — Acceptance Criteria & Test Plan | 0 | 0 | idem |
| 6 — Code Migration (semua fase A-G2) | 1 | 0 | 1 prompt: pilihan mode eksekusi G1 (checkpoint yang memang didesain untuk tanya). |
| 7 — Data Migration Scripts | 0 | 0 | N/A, port kode saja |
| 8 — Code Review | 0 | 0 | |
| 9 — Dev Testing | 0 | 0 | |
| 10 — QA Testing | 0 | 0 | |
| 11 — UAT Sign-off | 0 | 0 | Draft skrip UAT ditulis AI; sign-off sesungguhnya menunggu eksekusi manusia (di luar hitungan prompt AI) |
| **Total** | **7** | **0** | |

## Catatan Definisi

Tidak ada revisi kriteria klasifikasi selama project ini.

## Ringkasan Akhir Project

- Step dengan rasio Tool-fix tertinggi: Tidak ada (0 Tool-fix di semua step) — semua keputusan project ini bersifat instance-specific, tidak ada perubahan ke `migration-tool` itu sendiri selama kerja normal (konsisten aturan "AI TIDAK PERNAH tulis langsung ke templates/knowledge").
- Step yang paling "bersih" (Normal tinggi, Tool-fix 0): Step 2-5 dan 7-11 — **0 prompt sama sekali** setelah bootstrap selesai. Ini data poin kuat untuk kandidat otomasi: begitu Step 1 intake (termasuk bootstrap) selesai dikonfirmasi, seluruh Step 2 sampai Step 10 berjalan tanpa henti tanpa perlu campur tangan user — modul ini genuinely sederhana (satu rename + bump manifest), tapi pola "JALAN TERUS" yang didesain `USAGE_GUIDE.md` terbukti bekerja penuh di project ini, 0 interupsi di luar 1 checkpoint G1 yang memang didesain untuk tanya.
- Kandidat tool-fix yang MUNCUL tapi belum dieksekusi (lihat `migration-records/advanced_sales_analysis_18.0_19.0/SUMMARY.md`): dokumentasi `01a_MIGRATION_INTAKE.md`/`CLAUDE_TEMPLATE.md` §Folder belum mengantisipasi struktur `native-target` gabungan Community+Enterprise satu folder — AI harus tanya balik ke dev untuk klarifikasi struktur (bukan blocking, tapi memperlambat sedikit di bootstrap). Kandidat konkret untuk sesi curation berikutnya.
- Lihat `ai-doc/ROADMAP.md` §5 di `migration-tool` — tulis balik ringkasan project ini ke tabel agregat di sana begitu project ini selesai (di luar scope kerja normal, butuh sesi curation terpisah).
