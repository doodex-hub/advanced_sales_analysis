# -*- coding: utf-8 -*-
"""Step 04 — AC-07-* (SQL view sale.report).

CATATAN WAJIB: `sale.report` adalah model `_auto=False` yang membaca tabel `sale_order_line`
LANGSUNG lewat SQL — mem-bypass cache ORM. Setiap test di sini WAJIB memanggil
`self.env.flush_all()` sebelum query, kalau tidak nilai stored-compute yang baru ditulis di
transaksi yang sama belum ada di database dan hasilnya nol/nilai lama.
Lihat doc-dev-backfill/records/advanced_sales_analysis/SUMMARY.md CAND-03.
"""

from odoo.tests import tagged

from .common import AdvancedSalesAnalysisCommon


@tagged('post_install', '-at_install')
class TestAsaSaleReport(AdvancedSalesAnalysisCommon):

    def _report_rows(self, order):
        self.env.flush_all()
        return self.env['sale.report'].search([('order_reference', '=', f'sale.order,{order.id}')])

    def test_ac_07_01_kolom_baru_cocok_dengan_baris_so(self):
        order = self._make_so()
        invoice = self._invoice_so(order)
        self._pay(invoice)
        order.order_line.invalidate_recordset()
        expected = order.order_line.amount_received

        rows = self._report_rows(order)
        self.assertTrue(rows, "tidak ada baris sale.report untuk order ini")
        self.assertAlmostEqual(sum(rows.mapped('amount_received')), expected)
        self.assertAlmostEqual(expected, 100.0)

    def test_ac_07_01b_waiting_dan_to_invoice_muncul_di_laporan(self):
        order = self._make_so()
        self._invoice_so(order)
        order.order_line.invalidate_recordset()

        rows = self._report_rows(order)
        self.assertAlmostEqual(sum(rows.mapped('waiting_for_payment')), 100.0)
        self.assertAlmostEqual(sum(rows.mapped('amount_to_invoice')), 0.0)

    def test_ac_07_01c_flush_wajib_sebelum_query(self):
        """Membuktikan CAND-03: tanpa flush, SQL view membaca nilai lama."""
        order = self._make_so()
        invoice = self._invoice_so(order)
        self._pay(invoice)
        order.order_line.invalidate_recordset()
        self.assertAlmostEqual(order.order_line.amount_received, 100.0)

        self.env.flush_all()
        rows = self.env['sale.report'].search(
            [('order_reference', '=', f'sale.order,{order.id}')],
        )
        self.assertAlmostEqual(sum(rows.mapped('amount_received')), 100.0)

    def test_ac_07_02_baris_tanpa_product_id(self):
        """Baris section/note (`display_type` di-set) tidak masuk view sama sekali.

        `_where_sale()` core memfilter `l.display_type IS NULL`, jadi guard
        `CASE WHEN l.product_id IS NOT NULL` di modul ini praktis tidak pernah kena baris
        section/note — direkam apa adanya di sini.
        """
        order = self._make_so()
        self.env['sale.order.line'].create({
            'order_id': order.id,
            'name': 'Section uji',
            'display_type': 'line_section',
        })
        rows = self._report_rows(order)
        self.assertEqual(
            len(rows), 1,
            "baris section ternyata ikut masuk sale.report — perbarui dokumentasi AC-07-02",
        )

    def test_ac_07_03_group_by_granularitas_18_0(self):
        """F-06 (17.0) — DIPERBAIKI 2026-08-21 (F-19 fix): 3 kolom baru modul ini dipindah dari
        override manual `_select_sale()`/`_group_by_sale()` ke hook resmi
        `_select_additional_fields()`. Modul ini TIDAK LAGI ikut menyumbang kolom apa pun ke
        GROUP BY core (baik di 17.0 maupun 18.0) — soal apakah dua baris menyatu atau terpecah
        sekarang 100% ditentukan oleh `_group_by_sale()` CORE, bukan modul ini.

        MF-01 (migrasi 17.0->18.0, `doc-dev/migration_17.0_18.0/doc/FINDINGS.md`) — DIPUTUSKAN
        Opsi 1, disetujui pemilik modul 2026-08-21: core `sale.report._group_by_sale()` 18.0
        MENAMBAH kolom `l.price_unit`/`l.invoice_status`/`l.is_downpayment` ke GROUP BY (tidak ada
        di 17.0). Skenario test ini (dua baris produk sama, `price_unit` BEDA: 60.0 vs 40.0)
        akibatnya terpecah jadi 2 baris laporan di 18.0 — di 17.0 baris ini menyatu jadi 1 (karena
        `price_unit` belum jadi bagian GROUP BY 17.0). Ini perubahan behavior CORE Odoo yang
        disengaja diterima apa adanya (bukan bug modul, bukan sesuatu yang "diperbaiki" balik) —
        assertion di bawah mendokumentasikan baseline 18.0 yang BENAR, BUKAN nilai yang sama
        dengan 17.0 (`01_intake/01a_MIGRATION_INTAKE.md` §5, penyimpangan yang disetujui eksplisit).
        """
        order = self._make_so(lines=[
            (self.asa_product, 1.0, 60.0),
            (self.asa_product, 1.0, 40.0),
        ])
        rows = self._report_rows(order)
        self.assertEqual(
            len(rows), 2,
            "MF-01: granularitas 18.0 harus 2 baris (price_unit beda -> core GROUP BY memisahkan "
            "sejak 18.0) — kalau balik jadi 1, core Odoo berubah lagi atau modul ini tanpa sengaja "
            "menambah override _group_by_sale() manual (dilarang, lihat FINDINGS.md MF-01 Opsi 2).",
        )

    def test_f19_union_kompatibel_dengan_point_of_sale(self):
        """F-19 — REGRESI TEST untuk bug UNION column mismatch yang ditemukan post-backfill
        (production demo17.doodex.net 2026-08-20, dikonfirmasi ulang di fsdemo17/demo17_odoo_store
        2026-08-21 lewat tes langsung install/uninstall `point_of_sale`).

        Root cause: `point_of_sale` (via `pos_sale/report/sale_report.py`) meng-override `_query()`
        `sale.report` dan menambah `UNION ALL` cabang kedua lewat `_select_pos()` — yang JUGA
        memanggil `_select_additional_fields()` (mengisi field tak dikenal dengan `NULL`). Modul
        ini SEBELUMNYA menambah 3 kolom lewat override manual `_select_sale()` yang HANYA masuk ke
        cabang pertama UNION -> jumlah kolom dua cabang UNION berbeda -> psycopg2.errors.SyntaxError
        "each UNION query must have the same number of columns" setiap kali laporan Sales Analysis
        dibuka, KHUSUS ketika `point_of_sale` juga terinstall di database yang sama.

        Fix: pindahkan 3 kolom ke `_select_additional_fields()` (lihat models/sale_report.py) —
        hook ini otomatis ikut dipakai `_select_pos()` juga, jadi kedua cabang UNION selalu punya
        jumlah kolom yang sama, dengan atau tanpa `point_of_sale`.

        CATATAN ENVIRONMENT: test ini hanya berjalan jika `point_of_sale` sudah terinstall di
        database. Menginstall modul di dalam TransactionCase dilarang Odoo 17. Di environment
        backfill standar (`odoo:17.0` tanpa POS), test ini di-skip — itu perilaku yang diharapkan.
        Untuk verifikasi penuh F-19, jalankan di database dengan POS terinstall (mis. fsdemo17).
        """
        pos_module = self.env['ir.module.module'].search([('name', '=', 'point_of_sale')], limit=1)
        if not pos_module or pos_module.state != 'installed':
            self.skipTest(
                "point_of_sale tidak terinstall di environment ini — F-19 regression guard "
                "di-skip. Jalankan di database dengan POS terinstall untuk verifikasi penuh."
            )

        order = self._make_so()
        self._invoice_so(order)
        order.order_line.invalidate_recordset()

        try:
            rows = self._report_rows(order)
        except Exception as exc:  # noqa: BLE001 - sengaja tangkap semua, ini regression guard
            self.fail(
                "F-19 REGRESI — query sale.report gagal dengan point_of_sale terinstall "
                f"(kemungkinan UNION column mismatch lagi): {exc}"
            )

        self.assertTrue(rows, "tidak ada baris sale.report untuk order ini dengan point_of_sale terinstall")

    def test_ac_07_04_kolom_baru_tidak_dikonversi_mata_uang(self):
        """F-05: kolom core dikonversi ke mata uang perusahaan, kolom baru tidak.

        SO dalam mata uang berbeda dari mata uang perusahaan, dengan kurs 1:2.
        """
        company_currency = self.env.company.currency_id
        other_currency = self.env['res.currency'].with_context(active_test=False).search(
            [('name', '=', 'EUR')], limit=1,
        )
        if not other_currency or other_currency == company_currency:
            self.skipTest("mata uang pembanding tidak tersedia di database ini")
        other_currency.active = True
        self.env['res.currency.rate'].search([('currency_id', '=', other_currency.id)]).unlink()
        self.env['res.currency.rate'].create({
            'name': '2026-01-01',
            'currency_id': other_currency.id,
            'company_id': self.env.company.id,
            'rate': 2.0,
        })

        pricelist = self.env['product.pricelist'].create({
            'name': 'ASA Other Currency',
            'currency_id': other_currency.id,
        })
        order = self.env['sale.order'].create({
            'partner_id': self.partner_a.id,
            'pricelist_id': pricelist.id,
            'date_order': '2026-06-01',
            'order_line': [(0, 0, {
                'product_id': self.asa_product.id,
                'product_uom_qty': 1.0,
                'price_unit': 100.0,
            })],
        })
        order.action_confirm()
        invoice = self._invoice_so(order)
        self._pay(invoice)
        order.order_line.invalidate_recordset()

        rows = self._report_rows(order)
        self.assertTrue(rows)
        price_subtotal_report = sum(rows.mapped('price_subtotal'))
        amount_received_report = sum(rows.mapped('amount_received'))
        # price_subtotal core dikonversi 100 EUR -> 50 (mata uang perusahaan).
        self.assertAlmostEqual(price_subtotal_report, 50.0, places=2)
        # amount_received TIDAK dikonversi -> tetap 100 (nilai mata uang order).
        self.assertAlmostEqual(
            amount_received_report, 100.0, places=2,
            msg="amount_received ternyata ikut dikonversi — perbarui FINDINGS.md F-05",
        )
