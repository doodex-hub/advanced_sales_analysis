# -*- coding: utf-8 -*-
"""Setup bersama untuk test BACKFILL advanced_sales_analysis.

Ditulis Step 04 (BACKFILL, 2026-08-18). Semua helper di sini murni level test transaction —
tidak ada yang menyentuh kode bisnis modul.
"""

from odoo.fields import Command
from odoo.addons.sale.tests.common import TestSaleCommon


class AdvancedSalesAnalysisCommon(TestSaleCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Produk tanpa pajak supaya angka di assertion tetap bulat dan mudah dilacak.
        cls.asa_product = cls.env['product.product'].create({
            'name': 'ASA Service',
            'type': 'service',
            'invoice_policy': 'order',
            'list_price': 100.0,
            'taxes_id': [Command.clear()],
        })
        cls.asa_product_b = cls.env['product.product'].create({
            'name': 'ASA Service B',
            'type': 'service',
            'invoice_policy': 'order',
            'list_price': 100.0,
            'taxes_id': [Command.clear()],
        })
        cls.asa_product_delivery = cls.env['product.product'].create({
            'name': 'ASA Delivered',
            'type': 'service',
            'invoice_policy': 'delivery',
            'list_price': 100.0,
            'taxes_id': [Command.clear()],
        })

        # Modul mendeteksi baris uang muka lewat NAMA produk (lihat F-04) — dua produk di bawah
        # sengaja dibuat untuk menguji perilaku itu apa adanya.
        cls.asa_product_dp = cls.env['product.product'].create({
            'name': 'Down payment',
            'type': 'service',
            'invoice_policy': 'order',
            'list_price': 30.0,
            'taxes_id': [Command.clear()],
        })
        cls.asa_product_dp_fr = cls.env['product.product'].create({
            'name': 'Acompte',
            'type': 'service',
            'invoice_policy': 'order',
            'list_price': 30.0,
            'taxes_id': [Command.clear()],
        })

    # ------------------------------------------------------------------
    # helper
    # ------------------------------------------------------------------

    def _make_so(self, lines=None, confirm=True):
        """Buat (dan opsional konfirmasi) sale order sederhana.

        :param lines: list of (product, qty, price_unit); default satu baris 1 x 100.
        """
        if lines is None:
            lines = [(self.asa_product, 1.0, 100.0)]
        order = self.env['sale.order'].create({
            'partner_id': self.partner_a.id,
            'order_line': [
                Command.create({
                    'product_id': product.id,
                    'product_uom_qty': qty,
                    'price_unit': price,
                })
                for product, qty, price in lines
            ],
        })
        if confirm:
            order.action_confirm()
        return order

    def _invoice_so(self, order, post=True):
        invoice = order._create_invoices()
        if post:
            invoice.action_post()
        return invoice

    def _pay(self, invoice, amount=None):
        """Daftarkan pembayaran untuk invoice. `amount=None` berarti bayar penuh."""
        wizard_vals = {'payment_date': invoice.invoice_date or invoice.date}
        if amount is not None:
            wizard_vals['amount'] = amount
        wizard = self.env['account.payment.register'].with_context(
            active_model='account.move', active_ids=invoice.ids,
        ).create(wizard_vals)
        return wizard._create_payments()

    def _make_invoice(self, lines, move_type='out_invoice', post=True):
        """Buat invoice/credit note langsung (tanpa SO) dengan baris yang ditentukan.

        :param lines: list of (product, qty, price_unit)
        """
        invoice = self.env['account.move'].create({
            'move_type': move_type,
            'partner_id': self.partner_a.id,
            'invoice_date': '2026-01-01',
            'invoice_line_ids': [
                Command.create({
                    'product_id': product.id,
                    'quantity': qty,
                    'price_unit': price,
                    'tax_ids': [Command.clear()],
                })
                for product, qty, price in lines
            ],
        })
        if post:
            invoice.action_post()
        return invoice
