# Test Plan (Migrasi) — advanced_sales_analysis

**Step:** 5 — Acceptance Criteria & Test Plan
**Ref:** `05_acceptance/05a_MIGRATION_ACCEPTANCE_CRITERIA.md`
**Tanggal:** 2026-09-24

Environment: `docker-env/` (Odoo 20.0 from source `odoo20`, Postgres 15, Chrome headless). Run A = Community addons-path (setara baseline 19.0 `odoo:19.0`). Run B = `ASA_ADDONS_PATH=/odoo20/addons,/enterprise20,/mnt/extra-addons` (Enterprise-like, produksi dev = Enterprise). Wajib `docker compose down -v` sebelum tiap run.

## Step 9 — Dev Testing

| AC | Deskripsi | Unit | Integration | Tour (Owl/JS) |
|---|---|---|---|---|
| AC-01-01 | Install + test benar-benar jalan | — | G1 log (Run A & B) | — |
| AC-01-02 | Measures di pivot | — | `HttpCase.browser_js` (Chrome headless) | N/A (tidak ada tour; browser_js setara) |
| AC-02-* | kolisi `amount_paid` | `test_account_move` (5) | — | — |
| AC-03-* | komponen DP | `test_account_move` (8) | — | — |
| AC-04-* | `amount_received` | `test_sale_order_line` (7) | — | — |
| AC-05-* | `waiting_for_payment` | `test_sale_order_line` (5) | — | — |
| AC-06-* | `asa_amount_to_invoice` | `test_sale_order_line` (6) | — | — |
| AC-07-01…04, 06 | `sale.report` | — | `test_sale_report` (8, SQL view nyata) | — |
| AC-07-05 | UNION POS | — | skip (POS tidak terinstall) — gap warisan | — |

## Step 10 — QA Testing

| AC | Deskripsi | Manual | AI-interaktif | AI+tool eksternal |
|---|---|---|---|---|
| AC-01-02, AC-07-01 | Alur bisnis: SO → faktur → bayar sebagian → cek pivot 3 measure | Opsional (dev) | **Ya** — Playwright MCP/browser pane ke server G2 (`--http-interface=0.0.0.0`, port 8080) | — |
| AC-07-04 | Mata uang lain | — | Tercakup test otomatis | — |
| AC-07-05 | POS terinstall | — | Opsional: run tambahan dengan `-i advanced_sales_analysis,pos_sale` untuk mengamati MF-02 (bukan gate) | — |

## Step 11 — UAT

| Kelompok fitur | AC tercakup | UAT |
|---|---|---|
| Sales Analysis 3 measure | AC-01-02, AC-07-* | Manual oleh dev/PM (skrip di `11_UAT_CHECKLIST.md`); kalau dev memilih, sign-off berbasis bukti test AI (preseden 18→19, penyimpangan eksplisit) |
| Perhitungan per baris SO & faktur | AC-02…AC-06 | Idem |

## Ringkasan

| Step | Role | Tipe | Eksekusi | Jumlah AC |
|---|---|---|---|---|
| 9 | Developer (AI) | Unit/Integration/browser_js | Otomatis (Docker) | 38 |
| 10 | QA (AI) | AI-interaktif (browser) | Server G2 | 3 alur |
| 11 | PM/FA/User | UAT | Manual | 2 kelompok |
