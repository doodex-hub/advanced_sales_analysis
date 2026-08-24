# -*- coding: utf-8 -*-
"""Step 04 — AC-01-03, AC-02-*, AC-03-* (field pembantu di account.move).

Test ini MEREKAM perilaku yang terjadi sekarang (termasuk yang kemungkinan bug), bukan memaksa
perilaku yang "seharusnya" — sesuai prinsip BACKFILL.
"""

from odoo.tests import tagged

from .common import AdvancedSalesAnalysisCommon


@tagged('post_install', '-at_install')
class TestAsaAccountMove(AdvancedSalesAnalysisCommon):

    # ------------------------------------------------------------------
    # AC-01-03 — tabrakan dengan account_payment
    # ------------------------------------------------------------------

    def test_ac_01_03_account_payment_terinstall_bersama(self):
        """F-01: `account_payment` (auto_install pada `account`) memang ikut terinstall."""
        module = self.env['ir.module.module'].search([('name', '=', 'account_payment')])
        self.assertTrue(module, "modul account_payment tidak ditemukan di daftar modul")
        self.assertEqual(
            module.state, 'installed',
            "account_payment TIDAK terinstall — prasyarat tabrakan F-01 tidak terpenuhi di DB ini",
        )

    def test_ac_01_03_definisi_amount_paid_yang_menang(self):
        """F-01: definisi field mana yang efektif menang di registry.

        `account_payment` mendefinisikan `amount_paid` sebagai Monetary NON-stored
        (compute dari `transaction_ids`); modul ini mendefinisikannya sebagai Float STORED.
        """
        field = self.env['account.move']._fields['amount_paid']
        self.assertEqual(field.type, 'float', "tipe field bukan float — bukan definisi modul ini")
        self.assertTrue(field.store, "field tidak stored — bukan definisi modul ini")
        self.assertIn(
            'transaction_ids', self.env['account.move']._fields,
            "account_payment tidak aktif di model ini",
        )

    def test_ac_01_03_semantik_amount_paid_bukan_semantik_account_payment(self):
        """F-01: buktikan semantiknya benar-benar tergantikan, bukan sekadar beda tipe.

        Invoice tanpa satu pun `payment.transaction` tapi sudah lunas lewat jurnal:
        - semantik `account_payment` -> 0.0 (tidak ada transaksi online)
        - semantik modul ini        -> amount_total - amount_residual
        """
        order = self._make_so()
        invoice = self._invoice_so(order)
        self._pay(invoice)
        invoice.invalidate_recordset()

        self.assertFalse(invoice.transaction_ids, "prasyarat: tidak boleh ada payment.transaction")
        self.assertEqual(invoice.payment_state, 'paid')
        self.assertAlmostEqual(
            invoice.amount_paid, invoice.amount_total - invoice.amount_residual,
            msg="amount_paid tidak mengikuti semantik modul ini",
        )
        self.assertAlmostEqual(invoice.amount_paid, 100.0)

    # ------------------------------------------------------------------
    # AC-02-01 / AC-02-02 — jalur yang memang ter-assign
    # ------------------------------------------------------------------

    def test_ac_02_01_amount_paid_out_invoice_lunas(self):
        order = self._make_so()
        invoice = self._invoice_so(order)
        self._pay(invoice)
        invoice.invalidate_recordset()
        self.assertAlmostEqual(invoice.amount_paid, 100.0)

    def test_ac_02_02_amount_paid_cn_out_refund_lunas(self):
        credit_note = self._make_invoice(
            [(self.asa_product, 1.0, 40.0)], move_type='out_refund',
        )
        self._pay(credit_note)
        credit_note.invalidate_recordset()
        self.assertEqual(credit_note.payment_state, 'paid')
        self.assertAlmostEqual(credit_note.amount_paid_cn, 40.0)

    # ------------------------------------------------------------------
    # AC-02-03 / AC-02-04 — cabang yang TIDAK meng-assign (F-02)
    # ------------------------------------------------------------------

    def test_ac_02_03_move_type_entry_tidak_assign(self):
        """F-02: jurnal umum tidak masuk cabang mana pun di `_compute_amount_paid`."""
        journal = self.company_data['default_journal_misc']
        account = self.company_data['default_account_revenue']
        move = self.env['account.move'].create({
            'move_type': 'entry',
            'journal_id': journal.id,
            'date': '2026-01-01',
            'line_ids': [
                (0, 0, {'account_id': account.id, 'debit': 100.0, 'credit': 0.0}),
                (0, 0, {'account_id': account.id, 'debit': 0.0, 'credit': 100.0}),
            ],
        })
        move.flush_recordset()
        move.invalidate_recordset()
        # Perilaku yang direkam: nilai tidak pernah ditugaskan -> tersimpan NULL / dibaca 0.0,
        # TANPA error. Lihat FINDINGS.md F-02 untuk pembahasan risikonya.
        self.assertEqual(move.amount_paid, 0.0)
        self.assertEqual(move.amount_paid_cn, 0.0)
        self.env.cr.execute(
            "SELECT amount_paid, amount_paid_cn FROM account_move WHERE id = %s", (move.id,),
        )
        row = self.env.cr.fetchone()
        self.assertEqual(
            row, (None, None),
            "nilai di database ternyata bukan NULL — perilaku F-02 berubah, perbarui FINDINGS.md",
        )

    def test_ac_02_04_out_invoice_belum_dibayar_tidak_assign(self):
        """F-02: `out_invoice` ber-`payment_state == 'not_paid'` juga tidak ter-assign."""
        order = self._make_so()
        invoice = self._invoice_so(order)
        invoice.invalidate_recordset()
        self.assertEqual(invoice.payment_state, 'not_paid')
        self.env.cr.execute(
            "SELECT amount_paid FROM account_move WHERE id = %s", (invoice.id,),
        )
        self.assertEqual(
            self.env.cr.fetchone()[0], None,
            "amount_paid ternyata ter-assign untuk faktur belum dibayar — perbarui FINDINGS.md",
        )

    # ------------------------------------------------------------------
    # AC-03-* — komponen uang muka
    # ------------------------------------------------------------------

    def test_ac_03_01_dp_positif_belum_dibayar(self):
        invoice = self._make_invoice([(self.asa_product_dp, 1.0, 30.0)])
        invoice.invalidate_recordset()
        self.assertAlmostEqual(invoice.amount_dp2_nopaid, 30.0)
        self.assertAlmostEqual(invoice.amount_dp2, 0.0)

    def test_ac_03_02_dp_negatif_sudah_dibayar(self):
        invoice = self._make_invoice([
            (self.asa_product, 1.0, 100.0),
            (self.asa_product_dp, 1.0, -30.0),
        ])
        self._pay(invoice)
        invoice.invalidate_recordset()
        self.assertEqual(invoice.payment_state, 'paid')
        self.assertAlmostEqual(invoice.amount_dp, -30.0)
        self.assertAlmostEqual(invoice.amount_dp_nopaid, 0.0)

    def test_ac_03_03_dua_baris_dp_hanya_yang_terakhir_menang(self):
        """F-10: penugasan pakai `=` bukan `+=`, di luar loop."""
        invoice = self._make_invoice([
            (self.asa_product_dp, 1.0, 30.0),
            (self.asa_product_dp, 1.0, 50.0),
        ])
        invoice.invalidate_recordset()
        self.assertAlmostEqual(
            invoice.amount_dp2_nopaid, 50.0,
            msg="bukan 50.0 — kalau hasilnya 80.0 berarti F-10 sudah diperbaiki, perbarui FINDINGS.md",
        )

    def test_ac_03_04_dp_terbayar_sebagian_dianggap_belum_dibayar(self):
        """F-11: `_compute_amount_dp` tidak memasukkan `payment_state == 'partial'`."""
        invoice = self._make_invoice([(self.asa_product_dp, 1.0, 30.0)])
        self._pay(invoice, amount=10.0)
        invoice.invalidate_recordset()
        self.assertEqual(invoice.payment_state, 'partial')
        self.assertAlmostEqual(invoice.amount_dp2_nopaid, 30.0)
        self.assertAlmostEqual(invoice.amount_dp2, 0.0)

    def test_ac_03_05_produk_dp_non_inggris_tidak_dikenali(self):
        """F-04: deteksi DP berbasis nama produk hardcoded `"Down payment"`."""
        invoice = self._make_invoice([(self.asa_product_dp_fr, 1.0, 30.0)])
        invoice.invalidate_recordset()
        self.assertAlmostEqual(
            invoice.amount_dp2_nopaid, 0.0,
            msg="produk 'Acompte' ternyata dikenali sebagai DP — perbarui FINDINGS.md F-04",
        )
        self.assertAlmostEqual(invoice.amount_dp2, 0.0)
        self.assertAlmostEqual(invoice.amount_dp, 0.0)
        self.assertAlmostEqual(invoice.amount_dp_nopaid, 0.0)

    # ------------------------------------------------------------------
    # F-13 — label field
    # ------------------------------------------------------------------

    def test_f13_label_field_duplikat(self):
        """F-13: label duplikat — Odoo sendiri sudah mem-WARNING ini saat instalasi."""
        move_fields = self.env['account.move']._fields
        labels = {
            name: move_fields[name].string
            for name in ('amount_dp', 'amount_dp2', 'amount_dp_nopaid', 'amount_dp2_nopaid')
        }
        self.assertEqual(
            len(set(labels.values())), 1,
            "label keempat field DP ternyata sudah dibedakan — perbarui FINDINGS.md F-13",
        )
        sol_fields = self.env['sale.order.line']._fields
        self.assertEqual(
            sol_fields['asa_amount_to_invoice'].string, sol_fields['amount_received'].string,
            "label amount_to_invoice ternyata sudah diperbaiki — perbarui FINDINGS.md F-13",
        )
