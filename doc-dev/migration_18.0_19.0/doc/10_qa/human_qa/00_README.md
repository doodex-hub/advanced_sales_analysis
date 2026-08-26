# Human QA Checklists — advanced_sales_analysis (migrasi 18.0 → 19.0)

**Sumber:** diturunkan dari skenario S-01 s/d S-04 di `../10_BUSINESS_FLOW_MIGRATION.md`. Kalau skenario/level di file itu berubah, regenerate 4 file di folder ini juga.

Modul ini murni backend (SQL view + compute) — tidak ada wizard/dialog, jadi tidak ada checklist "multi-dialog" khusus. Ketiga measure baru muncul otomatis di pivot Sales → Reporting → Sales Analysis, tidak butuh setup menu tambahan.

| File | Isi | Kapan dipakai |
|---|---|---|
| `01_SMOKE.md` | Instalasi bersih & laporan terbuka tanpa error | Re-cek super cepat sebelum deploy/hotfix |
| `02_MAIN_FLOW.md` | 3 measure baru & nilainya benar (termasuk order ber-pajak) | QA rutin |
| `03_DETAIL.md` | Uang muka & multi-currency (bug `[BSL-013]`/`[BSL-014]` yang DISENGAJA dipertahankan) | QA menyeluruh sebelum rilis besar |
| `04_NEGATIVE.md` | Fix DIFF-01 (`tax_id`→`tax_ids`) tidak merusak flow pajak normal | **WAJIB dijalankan minimal sekali sebelum UAT** — ini verifikasi visual satu-satunya untuk fix DIFF-01 |

**Kombinasi disarankan:** sebelum UAT (Step 11) — jalankan keempatnya, terutama `04_NEGATIVE.md`.
