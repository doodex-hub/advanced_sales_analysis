# Human QA — advanced_sales_analysis (Odoo 20.0)

Checklist re-verifikasi manual, tanpa AI/tooling. Diturunkan dari `../10_BUSINESS_FLOW_MIGRATION.md`.

| File | Level | Kapan dijalankan | Estimasi |
|---|---|---|---|
| `01_SMOKE.md` | Smoke | Tiap deploy/rilis — kalau gagal, STOP | ~3 menit |
| `02_MAIN_FLOW.md` | Main Flow | Tiap rilis | ~10 menit |
| `03_DETAIL.md` | Detail | Rilis besar / setelah upgrade Odoo | ~20 menit |
| `04_NEGATIVE.md` | Negative | Rilis besar | ~5 menit |

Prasyarat: Odoo 20.0 dengan modul `advanced_sales_analysis` terinstall, user dengan akses Sales Administrator + Accounting.
