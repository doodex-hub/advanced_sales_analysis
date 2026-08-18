# CLAUDE.md — advanced_sales_analysis (doc-dev backfill)

## Identitas

Kamu adalah **BACKFILL copilot** — tugasmu membuat dokumentasi dev standar Doodex secara
**retroaktif** untuk modul berikut:

- **Modul:** advanced_sales_analysis
- **Repo:** `advanced-sales-analysis-17` (root repo ≠ root addon — addon ada di sub-folder
  `advanced_sales_analysis/`)
- **Path addon:** `D:\Kuncoro\doodex\repo\advanced-sales-analysis-17\advanced_sales_analysis`
- **Odoo version:** 17.0 — diverifikasi lewat pipeline Bootstrap Git (2026-08-18):
  `git checkout -b backfill/17.0 origin/17.0`, lalu `find . -name "__manifest__.py"` →
  `advanced_sales_analysis/__manifest__.py` dengan `version: '17.0.1.0.0'`. Konsisten dengan nama
  folder repo. **Catatan penting:** branch `master` repo ini punya struktur BERBEDA (flat, isi addon
  langsung di root repo, `version: '0.1'`) — jangan pakai `master` sebagai basis backfill.
  Sesi BACKFILL sebelumnya (2026-08-14) salah asumsi versi 16.0; lihat
  `doc-dev-backfill/AI_CONTEXT.md` + `records/advanced_sales_analysis/SUMMARY.md`.
- **Depends:** `base`, `sale`, `account`, `sale_management`
- **External addons:** *(tidak ada)* — keempat dependency diverifikasi ADA di image Core
  `odoo:17.0` lewat `docker run --rm odoo:17.0 ls /usr/lib/python3/dist-packages/odoo/addons/`
  (Bootstrap step 2c, 2026-08-18).
- **Environment eksekusi:** Claude Code CLI — Step 04 = Mode C (AI jalankan test langsung),
  Step 07 = Mode E (Tour headless).
- **Status dokumentasi sebelum backfill:** tidak ada doc/tests sama sekali.
- **Git eksekusi:** Ya — dikonfirmasi eksplisit dev (2026-08-18). Branch `backfill/17.0`,
  commit atomik per step gate, push TETAP manual.
- **Git source ref:** `origin/17.0` — dipilih eksplisit dev dari 3 kandidat
  (`master` / `origin/17.0` / `origin/16.0`).
- **Mulai:** 2026-08-18

### Penyimpangan lokasi `tests/` — disengaja, dicatat

Konvensi BACKFILL menaruh `CLAUDE.md`, `doc-dev/backfill/`, `docker-env/`, `tests/` di root folder
sesi. Di repo ini root repo ≠ root addon, dan Odoo HANYA menemukan test lewat sub-package
`tests/` DI DALAM addon. Maka:

| Artefak | Lokasi di repo ini | Alasan |
|---|---|---|
| `CLAUDE.md` | root repo | konvensi BACKFILL |
| `doc-dev/backfill/` | root repo | konvensi BACKFILL |
| `docker-env/` | root repo | konvensi BACKFILL |
| `tests/` | `advanced_sales_analysis/tests/` | **wajib teknis Odoo** — test di root repo tidak akan pernah ditemukan `--test-enable` |

---

## Source of Truth & Forbidden Actions

**Source of truth:** kode `advanced_sales_analysis` yang berjalan sekarang adalah kebenaran mutlak.
Dokumentasikan apa yang SEKARANG terjadi — termasuk quirk/bug — bukan memperbaikinya.

**Dilarang mutlak:** mengubah `models/`, `controllers/`, `security/` (dan `views/`/`wizard/`/`data/`
kalau nanti ada); memperbaiki bug yang ditemukan; mengisi UAT/sign-off.

**Boleh:** menambah `advanced_sales_analysis/tests/*.py`, menjalankannya, setup/stub ringan di level
test transaction.

Detail lengkap prinsip, batas workaround test-only, cek wajib Step 01/07, dan format `FINDINGS.md`:
`doc-dev-backfill/templates/CLAUDE_TEMPLATE.md` + `doc-dev-backfill/ai-doc/PLAYBOOK.md`.

---

## Provenance Tag

| Tag | Arti |
|---|---|
| `[HASIL-BACA]` | Murni hasil membaca kode, belum dikonfirmasi manusia — default |
| `[DIKONFIRMASI]` | Sudah dikonfirmasi pemilik modul sesuai intent |
| `[PERLU-KEPUTUSAN]` | Kandidat bug/ambigu — WAJIB juga masuk `FINDINGS.md` |

---

## Alur kerja

| Step | Output di `doc-dev/backfill/` | Gate? |
|---|---|---|
| 01 — Spec | `spec/01A_FUNCTIONAL_SPEC.md`, `spec/01B_ACCEPTANCE_CRITERIA.md` | Tidak formal |
| 03B — Test Plan | `test/03B_TEST_PLAN.md` | Tidak |
| 04 — Dev Testing | `test/04A_DEV_TESTING.md`, `advanced_sales_analysis/tests/*.py` | **Ya** |
| 07 — QA Testing | `test/07_QA_TESTING.md` | **Ya** |

Tidak ada step 06/08/09 — di luar scope BACKFILL.

---

## Status saat ini

**Backfill SELESAI sampai Step 07** (sesi kontinu CLI 01→07, 2026-08-18, satu sesi).
`0 failed, 0 error(s) of 37 tests`. 18 finding tercatat di `doc-dev/backfill/FINDINGS.md`, 4 di
antaranya prioritas Tinggi. Tidak ada sign-off — keputusan atas findings ada di pemilik modul.

Yang belum dilakukan (sengaja, bukan terlewat): `git push`. Branch `backfill/17.0` ada di lokal
saja — command push diserahkan ke dev.

### Status per Step

| Step | Dokumen | Status | Gate |
|---|---|---|---|
| 01 | `01A_FUNCTIONAL_SPEC.md`, `01B_ACCEPTANCE_CRITERIA.md` | ✅ Selesai ditulis | — |
| 03B | `03B_TEST_PLAN.md` | ✅ Selesai ditulis | — |
| 04 | `04A_DEV_TESTING.md`, `advanced_sales_analysis/tests/*.py` | ✅ Selesai ditulis | ✔️ Lulus — 36 test dijalankan nyata |
| 07 | `07_QA_TESTING.md` | ✅ Selesai ditulis | ✔️ Lulus — 9 skenario + Chrome headless, findings + `records/` sudah ditulis |

Legenda: ⬜ Belum mulai · 🔄 Sedang dikerjakan · ✅ Selesai ditulis · ✔️ Lulus gate.
