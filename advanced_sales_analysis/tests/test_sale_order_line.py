# -*- coding: utf-8 -*-
"""Step 04 — AC-04-*, AC-05-*, AC-06-* (tiga stored compute di sale.order.line)."""

from odoo.fields import Command
from odoo.tests import tagged

from .common import AdvancedSalesAnalysisCommon


@tagged('post_install', '-at_install')
class TestAsaSaleOrderLine(AdvancedSalesAnalysisCommon):

    # ------------------------------------------------------------------
    # AC-04-* — amount_received
    # ------------------------------------------------------------------

    def test_ac_04_01_received_penuh(self):
        order = self._make_so()
        invoice = self._invoice_so(order)
        self._pay(invoice)
        order.invalidate_recordset()
        order.order_line.invalidate_recordset()
        self.assertAlmostEqual(order.order_line.amount_received, 100.0)

    def test_ac_04_02_received_nol_kalau_belum_dibayar(self):
        order = self._make_so()
        self._invoice_so(order)
        order.order_line.invalidate_recordset()
        self.assertAlmostEqual(order.order_line.amount_received, 0.0)

    def test_ac_04_03_received_pembayaran_sebagian(self):
        order = self._make_so()
        invoice = self._invoice_so(order)
        self._pay(invoice, amount=60.0)
        invoice.invalidate_recordset()
        self.assertEqual(invoice.payment_state, 'partial')
        order.order_line.invalidate_recordset()
        self.assertAlmostEqual(order.order_line.amount_received, 60.0)

    def test_ac_04_04_received_proporsional_dua_baris(self):
        order = self._make_so(lines=[
            (self.asa_product, 1.0, 60.0),
            (self.asa_product_b, 1.0, 40.0),
        ])
        invoice = self._invoice_so(order)
        self._pay(invoice)
        order.order_line.invalidate_recordset()
        line_60 = order.order_line.filtered(lambda l: l.price_unit == 60.0)
        line_40 = order.order_line.filtered(lambda l: l.price_unit == 40.0)
        self.assertAlmostEqual(line_60.amount_received, 60.0)
        self.assertAlmostEqual(line_40.amount_received, 40.0)

    def test_ac_04_05_credit_note_mengurangi_received(self):
        order = self._make_so()
        invoice = self._invoice_so(order)
        self._pay(invoice)
        order.order_line.invalidate_recordset()
        self.assertAlmostEqual(order.order_line.amount_received, 100.0)

        reversal = self.env['account.move.reversal'].with_context(
            active_model='account.move', active_ids=invoice.ids,
        ).create({
            'journal_id': invoice.journal_id.id,
            'date': invoice.invoice_date,
        })
        reversal.reverse_moves()
        credit_note = reversal.new_move_ids
        credit_note.action_post()
        self._pay(credit_note)

        order.order_line.invalidate_recordset()
        self.assertAlmostEqual(
            order.order_line.amount_received, 0.0,
            msg="credit note lunas seharusnya menetralkan amount_received",
        )

    def test_ac_04_06_baris_dp_pakai_jalur_amount_dp(self):
        order = self._make_so(lines=[(self.asa_product_dp, 1.0, 30.0)])
        invoice = self._invoice_so(order)
        self._pay(invoice)
        order.order_line.invalidate_recordset()
        # Baris produk "Down payment" -> nilai diambil dari amount_dp2 + amount_dp - amount_refund
        # invoice-nya, BUKAN dari perhitungan proporsional.
        invoice.invalidate_recordset()
        expected = invoice.amount_dp2 + invoice.amount_dp - invoice.amount_refund
        self.assertAlmostEqual(order.order_line.amount_received, expected)

    def test_ac_04_07_faktur_untaxed_nol_tidak_error(self):
        """F-16: guard bagi-nol — pastikan tidak ada ZeroDivisionError, kontribusi 0."""
        order = self._make_so()
        invoice = order._create_invoices()
        invoice.invoice_line_ids.write({'discount': 100.0})
        invoice.action_post()
        self.assertAlmostEqual(invoice.amount_untaxed, 0.0)
        order.order_line.invalidate_recordset()
        self.assertAlmostEqual(order.order_line.amount_received, 0.0)
        self.assertAlmostEqual(order.order_line.waiting_for_payment, 0.0)

    # ------------------------------------------------------------------
    # AC-05-* — waiting_for_payment
    # ------------------------------------------------------------------

    def test_ac_05_01_waiting_penuh(self):
        order = self._make_so()
        self._invoice_so(order)
        order.order_line.invalidate_recordset()
        self.assertAlmostEqual(order.order_line.waiting_for_payment, 100.0)

    def test_ac_05_02_waiting_setelah_pembayaran_sebagian(self):
        order = self._make_so()
        invoice = self._invoice_so(order)
        self._pay(invoice, amount=60.0)
        order.order_line.invalidate_recordset()
        self.assertAlmostEqual(order.order_line.waiting_for_payment, 40.0)

    def test_ac_05_03_waiting_nol_kalau_belum_difakturkan(self):
        order = self._make_so()
        order.order_line.invalidate_recordset()
        self.assertAlmostEqual(order.order_line.waiting_for_payment, 0.0)

    def test_ac_05_04_faktur_cancel_diabaikan(self):
        order = self._make_so()
        invoice = self._invoice_so(order)
        order.order_line.invalidate_recordset()
        self.assertAlmostEqual(order.order_line.waiting_for_payment, 100.0)
        invoice.button_cancel()
        order.order_line.invalidate_recordset()
        self.assertAlmostEqual(
            order.order_line.waiting_for_payment, 0.0,
            msg="baris faktur yang di-cancel seharusnya tidak ikut dihitung",
        )

    def test_ac_05_05_dua_faktur_untuk_satu_baris_so(self):
        """F-09: guard akhir memakai `amount_residual` dari iterasi TERAKHIR saja.

        Skenario: satu baris SO (2 x 100) difakturkan dua kali, masing-masing 1 unit.
        Faktur A dibayar lunas, faktur B belum dibayar. Nilai yang direkam di sini jadi dasar
        pembahasan F-09 di FINDINGS.md.
        """
        order = self._make_so(lines=[(self.asa_product, 2.0, 100.0)])
        line = order.order_line

        invoice_a = order._create_invoices()
        invoice_a.invoice_line_ids.write({'quantity': 1.0})
        invoice_a.action_post()
        self._pay(invoice_a)

        invoice_b = order._create_invoices()
        invoice_b.action_post()

        line.invalidate_recordset()
        self.assertAlmostEqual(line.amount_received, 100.0)
        self.assertAlmostEqual(line.waiting_for_payment, 100.0)

    # ------------------------------------------------------------------
    # AC-06-* — amount_to_invoice
    # ------------------------------------------------------------------

    def test_ac_06_01_to_invoice_sebelum_difakturkan(self):
        order = self._make_so()
        order.order_line.invalidate_recordset()
        self.assertAlmostEqual(order.order_line.asa_amount_to_invoice, 100.0)

    def test_ac_06_02_to_invoice_setelah_lunas(self):
        order = self._make_so()
        invoice = self._invoice_so(order)
        self._pay(invoice)
        order.order_line.invalidate_recordset()
        self.assertAlmostEqual(order.order_line.asa_amount_to_invoice, 0.0)

    def test_ac_06_03_to_invoice_nol_kalau_draft(self):
        order = self._make_so(confirm=False)
        order.order_line.invalidate_recordset()
        self.assertEqual(order.state, 'draft')
        self.assertAlmostEqual(order.order_line.asa_amount_to_invoice, 0.0)

    def test_ac_06_04_invoice_policy_delivery_diabaikan(self):
        """F-17: `price_subtotal` lokal (yang menghormati `qty_delivered`) tidak pernah dipakai.

        Method menghitung `price_subtotal` lokal dari `qty_delivered` untuk produk
        ber-`invoice_policy == 'delivery'` (4 x 10 = 40), tapi cabang `else` terakhir memakai
        FIELD `line.price_subtotal` (10 x 10 = 100) — variabel lokalnya jadi dead code kecuali
        di cabang "diskon baris faktur berbeda". Ditemukan lewat eksekusi nyata, bukan baca kode.
        """
        order = self._make_so(lines=[(self.asa_product_delivery, 10.0, 10.0)])
        line = order.order_line
        line.qty_delivered = 4.0
        line.invalidate_recordset()
        self.assertAlmostEqual(
            line.asa_amount_to_invoice, 100.0,
            msg="kalau hasilnya 40.0, F-17 sudah diperbaiki — perbarui FINDINGS.md",
        )
        self.assertAlmostEqual(line.price_subtotal, 100.0)

    def test_ac_06_05_urutan_pembacaan_field_melingkar(self):
        """F-03: ketiga compute saling depends — cek apakah hasil bergantung urutan baca."""
        order = self._make_so()
        invoice = self._invoice_so(order)
        self._pay(invoice, amount=60.0)
        line = order.order_line

        line.invalidate_recordset()
        urutan_a = (line.asa_amount_to_invoice, line.waiting_for_payment, line.amount_received)

        line.invalidate_recordset()
        received_dulu = line.amount_received
        waiting_dulu = line.waiting_for_payment
        urutan_b = (line.asa_amount_to_invoice, waiting_dulu, received_dulu)

        self.assertEqual(
            urutan_a, urutan_b,
            "hasil BERBEDA tergantung urutan pembacaan field — bukti order-dependency F-03",
        )
