# Code Review — advanced_sales_analysis

**Step:** 8 — Code Review (gate)
**Ref:** `03_spec/03_MIGRATION_SPEC.md`, `05_acceptance/05a_MIGRATION_ACCEPTANCE_CRITERIA.md`, `06_implementation/06c_IMPLEMENTATION_LOG.md`, `01_intake/01b_BASELINE_SPEC.md`, `FINDINGS.md`
**Odoo Version:** 20.0
**Files reviewed:** `git diff migration/19.0 -- advanced_sales_analysis` pada working tree `migration/20.0` (base `migration/19.0` = `45c0319`): `__manifest__.py`, `models/sale_report.py`, `tests/test_sale_report.py`, `static/description/**` (aset biner/HTML, dibandingkan byte-identik dengan branch `19.0`). Kode framework dibaca dari `odoo20`/`enterprise20` lokal (checkout `20.0`, dibaca 2026-09-24).
**Tanggal:** 2026-09-24

---

## A. Issues

**Status skill `odoo-review` (WAJIB):**
- [x] Terinstall (`.claude/skills/odoo-review` + `odoo-guidelines`, `odoo-security`, `odoo-web-guidelines`) & sudah dijalankan 2026-09-24 — hasil digabung di tabel ini.

**Pemetaan file → section (skill `odoo-review` langkah Map):**
| File | Section dibaca |
|---|---|
| `__manifest__.py` | Manifest; Imports/Naming (N/A isi) |
| `models/sale_report.py` | Imports; Naming and model layout; Methods and extension points; Computes, onchange and constraints; Recordsets, domains and context; odoo-security "Use the ORM; parameterize SQL" |
| `tests/test_sale_report.py` | Tests; Imports; Naming |
| semua | Changes in a stable version — **dipertimbangkan tapi tidak diterapkan**: ini port ke rilis mayor baru (20.0), bukan fix di stable branch; tetap dijaga minimal-diff sesuai forbidden actions CLAUDE.md |

| ID | Severity | Kategori | File | Baris | Issue | Rekomendasi |
|---|---|---|---|---|---|---|
| CR-01 | 🔵 Info | Tests (*"Assert behavior, not implementation"*) | `tests/test_sale_report.py` | `test_ac_07_06_select_dict_hook_dipakai` | Test memeriksa implementasi (tidak ada `_select_additional_fields`, isi string `SQL._sql_tuple` — atribut privat framework). Rapuh kalau core mengganti internal `SQL`; skenario: refactor `odoo.tools.SQL` di 21.0 → test merah tanpa regresi bisnis. | Dipertahankan dengan sengaja sebagai regression guard migrasi (MF-01 silent); perilaku bisnisnya sendiri sudah dicakup AC-07-01/04. Hapus/ubah di migrasi berikutnya kalau rapuh. |
| CR-02 | 🔵 Info | Imports | `models/sale_report.py` | 4 | `from odoo import fields, models, api` tidak urut alfabet (pre-existing 19.0). Import baru `from odoo.tools import SQL` sudah di grup yang benar. | Tidak diubah (minimal-diff, bukan kewajiban kompatibilitas). |

**Rules pass — tidak ada pelanggaran lain:**
- SQL dibangun dengan wrapper `odoo.tools.SQL`, identifier kolom lewat `TableSQL` (`table.product_id`, `table.amount_received`) — tidak ada interpolasi string (odoo-security §parameterize SQL). Query berjalan di atas `sale.order.line._search()` milik core (sudo core, tidak ditambah modul).
- Override `_select_dict(table)` memanggil `super()` dan menggabung dict (`|`) — pola ekstensi yang sama dengan `sale_margin`/`sale_stock`/`website_sale`/`sale_project` 20.0 (Methods and extension points).
- Manifest: `version` semver 20.0.x; `depends` tidak berubah (catatan guideline "don't list base" — pre-existing, tidak diubah).
- Test baru di class `@tagged('post_install', '-at_install')` yang sudah ada, file `test_*.py` sudah di-import — tidak ada silent skip.

**Merits pass (skill langkah 5):**
- *Edge `product_id` NULL:* core `_order_line_domain()` membuang `display_type`; baris tanpa produk non-section praktis tidak ada → `ELSE 0` identik 19.0 (AC-07-02 PASS).
- *Validitas SQL `CASE` di luar agregat:* `table.product_id` ada di `_groupby_list()` core → valid; dibuktikan G1 #3.
- *Kurs:* tidak dikalikan `rate` → BSL-014 (AC-07-04 PASS: core 50, modul 100).
- *Downpayment:* guard modul `product_id IS NOT NULL` (bukan `is_downpayment IS NOT TRUE` core) → baris DP tetap dihitung seperti 19.0.
- *Konsumen yang tidak terlihat di diff:* (1) `sale.subscription.report` (Enterprise, `_inherit = ["sale.report"]` + `_name` baru) mewarisi 3 field & `_select_dict` modul lewat `super()` — paritas 19.0 (dulu lewat `super()._select_additional_fields()`), tabel tetap `sale.order.line`. (2) `pos_sale._select_pos_dict()` tidak memanggil `_select_dict` → cabang POS tidak memakai ekspresi modul (MF-02, diterima). (3) `partner_commission` (Enterprise) override `_select_dict` dengan key berbeda → komposabel.
- *Skala:* ekspresi `SUM` pada kolom stored, sama seperti 19.0; tidak ada query tambahan.
- *Klaim commit vs kode:* "port `_select_additional_fields` → `_select_dict`" — sesuai.

**Guidelines read:** Manifest, Imports, Naming and model layout, Translate only static literals, Recordsets domains and context, Computes onchange and constraints, Methods and extension points, Transactions and exceptions, Tests, Changes in a stable version, odoo-security (Use the ORM; parameterize SQL, Domain injection, Don't over-sudo).

## B. Gap Analysis — Implementasi vs Migration Spec

| Spec item | Implementasi | Status | Catatan |
|---|---|---|---|
| DIFF-07 / A1 manifest version | `20.0.1.0.0` | ✅ | |
| DIFF-09 / aset store `images` | `banner.gif` + `icon.png` | ✅ | identik branch `19.0` |
| aset `static/description` | `git diff 19.0 -- …/static/description` kosong | ✅ | |
| DIFF-01 / A5 `_select_dict` | 3 key, guard & tanpa kurs | ✅ | |
| Test (a)(b)(c)(d) spec §2 | docstring modul + 2 test baru; assertion lama tidak berubah | ✅ | (d) docstring f19 dicakup catatan modul-level |
| AccountMove/SaleOrderLine tidak diubah | `git diff` class tsb kosong | ✅ | |

## C. Gap Analysis — Implementasi vs Acceptance Criteria

| AC ID | Behavior | Status | Jejak Nalar | Catatan |
|---|---|---|---|---|
| AC-01-01 | install, test berjalan | ✅ | G1 #3: 43 test runner, 0 fail | |
| AC-01-02 | measure di pivot | ✅ | browser_js PASS | |
| AC-02-* … AC-06-* | compute tidak berubah | ✅ | kode identik 19.0 + test PASS | |
| AC-07-01/01b/01c/04 | nilai `sale.report` | ✅ | FAIL di probe → PASS setelah A5 (test benar-benar gagal tanpa fix) | |
| AC-07-02, 03 | granularitas core | ✅ | PASS | |
| AC-07-03b | MF-03 | ✅ | test baru PASS | perubahan core diterima |
| AC-07-05 | UNION POS | ⚠️ gap warisan | skip (POS tidak terinstall) | tetap terbuka (bukan regresi) |
| AC-07-06 | regression guard | ✅ | PASS | |

## D. Cek Khusus Migrasi — P1 Fidelity

- [x] Tidak ada perubahan behavior yang tidak disengaja. Deviasi yang tercatat & disetujui: MF-02 (POS, dev), MF-03 (granularitas core, preseden), aset store (dev).

**Tabrakan dengan core (empat arah):**
1. Arah 1 — method modul bernama sama dengan core: `_select_dict` (override sengaja, pakai `super()`); `_compute_amount_paid` menimpa `account_payment` (BSL-006, pre-existing, definisi core identik 19↔20). Tidak ada yang baru.
2. Arah 2 — definisi baru core 20.0 bernama sama dengan field/method modul: grep `odoo20` + `enterprise20` → 0 (lihat `02_DIFF_ANALYSIS.md` §1 akhir). Satu-satunya "tabrakan" baru: key `amount_to_invoice` di `pos_sale._select_pos_dict()` (MF-02, bukan field/method).
3. Arah 3 — N/A (tidak ada registry UI JS).
4. Arah 4 — N/A (tidak ada JS).
- [x] Sudah dicek (keempat arah).

## E. Perubahan Tak Tertelusuri

- [x] Tidak ada. `docker-env/` (infra test) tercatat di `06c` §Infra.

## F. Kontribusi ke Knowledge Base

- [x] Ada — `migration-records/advanced_sales_analysis_19.0_20.0/SUMMARY.md`: CAND-08 (prototype-inherit `sale.subscription.report` ikut mewarisi override `_select_dict` — cek paritas kalau produksi Enterprise).

## G. Verdict

- Ringkasan Issues: 0 🔴 · 0 🟡 · 2 🔵
- [x] ✅ Lulus — tidak ada 🔴, lanjut ke step 9 (2026-09-24)
