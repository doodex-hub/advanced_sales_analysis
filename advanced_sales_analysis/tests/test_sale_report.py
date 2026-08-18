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

    def test_ac_07_03_group_by_tambahan_memecah_baris(self):
        """F-06: tiga kolom baru ikut GROUP BY -> dua baris identik bisa TIDAK menyatu.

        Dua baris SO dengan produk SAMA, diskon SAMA, tapi nilai berbeda sehingga
        `amount_received`/`waiting_for_payment`/`amount_to_invoice`-nya berbeda.
        """
        order = self._make_so(lines=[
            (self.asa_product, 1.0, 60.0),
            (self.asa_product, 1.0, 40.0),
        ])
        rows = self._report_rows(order)
        self.assertEqual(
            len(rows), 2,
            "kedua baris menyatu jadi satu row — kalau begitu F-06 tidak berdampak seperti dugaan, "
            "perbarui FINDINGS.md",
        )

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
