# Migration Intake — advanced_sales_analysis

**Step:** 1 — Intake & Scope
**Versi:** 19.0 → 20.0
**Tanggal:** 2026-09-24
**Status:** ✔️ Disetujui — jawaban dev 2026-09-24 (sesi CLI, lewat dialog pertanyaan intake)

---

## 0. Folder Referensi

Semua path disebut dev langsung di prompt pembuka sesi 2026-09-24 ("pakai tool migration ...", "odoo core/community 20 ...", "odoo enterprise ...") dan sudah tercatat di `CLAUDE.md` sejak conditioning. Dicek `ls` 2026-09-24.

- [x] `native-target` (Community 20.0) — `D:\Kuncoro\doodex\repo\odoo20` (repo penuh, `odoo/addons/base` + `addons/`).
- [x] `native-source` (Community 19.0) — `D:\Kuncoro\doodex\repo\odoo19`.
- [x] `native-target-enterprise` — `D:\Kuncoro\doodex\repo\enterprise20` (addons-only, TERPISAH dari Community — bukan folder gabungan). Auto-scan §2 tidak menemukan dependency Enterprise; modul Community-only. Instance produksi dev jalan Enterprise (dikonfirmasi dev di project 18→19), jadi folder ini dipakai sebagai referensi + satu run test tambahan dengan `enterprise20` di addons-path (Step 9).
- [x] `native-source-enterprise` — `D:\Kuncoro\doodex\repo\enterprise19` (referensi saja).
- [x] `third-party-*` — tidak ada. Auto-scan: `depends` hanya `base, sale, account, sale_management`; tidak ada import pihak ketiga. Dikonfirmasi dev di project sebelumnya, tidak dikoreksi di sesi ini.

### 0a. Branch / Versi

- [x] Source: branch `migration/19.0` (repo ini, dibaca via `git show`/`git diff`; tidak ada folder `source-codebase` terpisah — desain conditioning 2026-09-24). **Dikonfirmasi dev 2026-09-24:** "source branch migration/19.0".
- [x] Target: branch `migration/20.0` (checkout aktif di `D:\Kuncoro\doodex\repo\advanced-sales-analysis-migration-20`). **Dikonfirmasi dev 2026-09-24:** "target migration/20.0".
- [x] Source & target bukan folder yang sama secara fisik? — N/A by design: satu repo, dua branch; source hanya dibaca via git object, tidak pernah di-checkout di working tree ini.
- [x] Versi semantik: **19.0 → 20.0** — dikonfirmasi dev ("Lakukan migrasi 19=>20").

### 0b. Path absolut `.claude/settings.json`

`settings.json` varian Mode Git sudah diisi saat conditioning: deny `Edit` untuk `odoo19`, `enterprise19`, `odoo20`, `enterprise20`, `migration-tool/knowledge/**`, `migration-tool/templates/**`. Tidak ada placeholder `{{ABS_PATH_...}}` tersisa (dicek 2026-09-24). Tidak ada `source-codebase` terpisah → tidak perlu rule untuk itu. Third-party: tidak ada → tidak ada baris.

---

## Ringkasan untuk Review — Perlu Konfirmasi User

Semua poin di bawah SUDAH dijawab dev 2026-09-24 (dialog intake). Dicatat di sini sebagai jejak keputusan.

1. **Sifat migrasi = port kode saja, source beku** — dev: "Ya, dua-duanya". Step 7 N/A, `SYNC_POLICY` tidak aktif.
2. **Aset store dari branch rilis `19.0` DI-PORT ke 20.0** — dev: "Ya, port aset store". Scope: `static/description/*` (banner.gif, icon.png, index.html baru, folder `assets/`) + key `images` di manifest (`banner.gif` + `icon.png`). Kode, test, dan docker-env TETAP dari `migration/19.0` (branch rilis `19.0` menghapus `tests/`/`docker-env/` lewat commit "cleaning" — penghapusan itu TIDAK ikut di-port). Perubahan non-fungsional, tidak menyentuh logic. Dicatat sebagai perubahan sengaja di §5.
3. **Temuan Step 1 (didahulukan dari Step 2 karena berdampak ke scope): hook `sale.report._select_additional_fields()` DIHAPUS di 20.0** (diganti `_select_dict(table)` berbasis `SQL`/`TableSQL`). Tanpa port, 3 measure modul diam-diam jadi `NULL` di laporan (tidak ada error). Port wajib — satu cara benar, tanpa trade-off bisnis.
4. **Efek samping POS (dev: "Terima & dokumentasikan")** — native `pos_sale` 20.0 mengisi key `amount_to_invoice` untuk baris POS di UNION `sale.report`; di 19.0 baris POS mendapat `NULL` untuk semua kolom modul. Karena modul mendefinisikan field `sale.report.amount_to_invoice`, kalau `pos_sale` terinstall nilai baris POS berubah dari NULL → subtotal POS yang belum difakturkan. Diterima apa adanya, dicatat sebagai finding (lanjutan gap AC-07-05, POS di luar dependency modul, tidak pernah dieksekusi di versi manapun). Tanpa override tambahan.
5. **Eksekusi:** GUI git client ditutup (dev konfirmasi 2026-09-24); AI menjalankan Docker sendiri (build Odoo 20 from source, G1, test suite, browser check) dan auto-commit per step di `migration/20.0` (tanpa push).

---

## 1. Modul & Scope

- Modul yang dimigrasi: `advanced_sales_analysis` (satu modul, subfolder `advanced_sales_analysis/`).
- Fungsi: menambah 3 measure finansial (Amount Received, Waiting for Payment, Amount To Invoice) ke Sales Analysis (`sale.report`), dihitung dari field stored-compute di `sale.order.line` yang bertumpu pada 8 field bantu di `account.move`.
- Saling depend dengan modul custom lain: tidak.

## 2. Dependency Map (auto-scan)

| Dependency | Tipe | Versi tersedia di target? | Catatan |
|---|---|---|---|
| `base` | Native Community | Ya (`odoo20/odoo/addons/base`) | — |
| `sale` | Native Community | Ya (`odoo20/addons/sale`) | `sale.report` dirombak total di 20.0 (lihat Step 2 DIFF-01) |
| `account` | Native Community | Ya | field yang dipakai (`amount_residual`, `payment_state`, `move_type`, `amount_untaxed`, `amount_total`, `invoice_line_ids`) ada; selection `payment_state` identik 19↔20 |
| `sale_management` | Native Community | Ya | tidak dipakai langsung di kode |

Dependency implisit / runtime:
- `account_payment` (Community, `auto_install` bareng `account`) — kolisi nama `account.move.amount_paid` (BSL-006), tetap ada di 20.0.
- `pos_sale` (Community, kalau terinstall) — UNION `sale.report`; lihat Ringkasan poin 4.
- Tidak ada `'x' in self.env` / import opsional di kode.

## 2b. Struktur & Fitur Modul (auto-scan)

| Fitur | Ada di modul? | Lokasi/bukti | Fase step 6 |
|---|---|---|---|
| Controllers (route custom) | Tidak | `controllers/controllers.py` hanya berisi komentar (`# from odoo import http`) | D1 N/A |
| Assets/CSS/JS custom | Tidak | tidak ada `static/src/`, tidak ada key `assets` | D2, E, F N/A |
| Komponen Owl/JS custom | Tidak | — | E, F N/A |
| Field JSON / relasi berantai / dynamic model | Tidak (relasi `invoice_lines.move_id.*` 3 level di `@api.depends`, tanpa field JSON/dynamic model) | `models/sale_report.py` | B2 → cek ringan |
| View dengan `attrs`/`states`/dinamis | Tidak (tidak ada view XML sama sekali) | `'data': []` | C1/C2 N/A |
| Security (`ir.model.access`) | File ada, TIDAK dimuat manifest (baris di-comment) | `security/ir.model.access.csv` | Relevan untuk DIFF `ir.access` 20.0 — tidak berdampak karena tidak dimuat (lihat Step 2) |

## 3. Sifat Migrasi

- [x] Port kode saja (instalasi baru di 20.0) — dikonfirmasi dev 2026-09-24.
- [ ] Upgrade instance

## 4. Baseline Spec / Characterization Test (gate)

- [x] `FUNCTIONAL_SPEC.md` lama: ada rantai spec sebelumnya di repo ini — `doc-dev/backfill/spec/01A_FUNCTIONAL_SPEC.md` (17.0) → `doc-dev/migration_17.0_18.0/doc/01_intake/01b_BASELINE_SPEC.md` → `doc-dev/migration_18.0_19.0/doc/01_intake/01b_BASELINE_SPEC.md` (baseline 18.0). Dipakai sebagai draft awal, di-cross-check ke kode `migration/19.0` aktual.
- [x] Test lama: ada, di lokasi yang SAMA dengan source (`advanced_sales_analysis/tests/`, 5 file, 39 test — hasil `doc-dev-backfill` 17.0 + update migrasi 17→18 dan 18→19). G1 terakhir di 19.0: `0 failed, 0 error(s) of 39 tests` (2026-08-26).
- [x] `01b_BASELINE_SPEC.md` diisi — lihat file itu.

### 4a. Dokumen Pelengkap Lain

- [x] Dokumen di repo: `README.md`, `LISEZMOI.md` (root & addon), dokumen migrasi sebelumnya di `doc-dev/`. Tidak ada dokumen di luar repo yang disebut dev di project ini maupun project 18→19 (dev tidak menyebut tambahan saat ditanya scope 2026-09-24). Jika ada, dev dapat menambahkan kapan saja — tidak memblokir.

## 4b. Source Masih Aktif Dikembangkan?

- [x] Tidak — `migration/19.0` beku (dev 2026-09-24). Catatan: branch rilis `19.0`/`staging/19.0` punya 5 commit pasca-migrasi (cleaning + aset store) — aset store di-port (Ringkasan poin 2), bukan dianggap pengembangan aktif.

## 5. Scope Boundary

- **Tetap identik:** seluruh business logic 3 compute `sale.order.line`, 2 compute `account.move`, isi & semantik 3 kolom `sale.report` (tanpa konversi mata uang, guard `product_id IS NOT NULL`), semua quirk BSL-011…BSL-021, nama field/method (termasuk `asa_amount_to_invoice`), label field (termasuk label duplikat/salah).
- **Sengaja diubah:**
  1. `__manifest__.py` `version` → `20.0.1.0.0` (wajib).
  2. `sale.report` hook `_select_additional_fields()` → `_select_dict(table)` (wajib kompatibilitas, DIFF-01).
  3. Aset store dari branch rilis `19.0` (`static/description/*` + key `images`) — keputusan dev 2026-09-24, non-fungsional.
  4. `docker-env/` diganti ke Odoo 20 from-source (infrastruktur test, bukan kode modul).
  5. Test yang bergantung pada granularitas GROUP BY core / struktur SQL core disesuaikan kalau core 20.0 mengubahnya (bukan perubahan behavior modul) — dicatat per test di Step 6.
- **Sengaja TIDAK diubah:** penghapusan `tests/`/`docker-env/` dari branch rilis `19.0` (commit "cleaning") tidak ikut di-port.

## 6. Constraint

- Deadline: tidak disebutkan — belum relevan, dilewati.
- Owner: dev (Kuncoro) untuk keputusan & push; AI untuk Step 1–11 eksekusi dokumen/kode/test.
