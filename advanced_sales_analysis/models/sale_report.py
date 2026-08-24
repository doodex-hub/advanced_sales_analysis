# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api

class SaleReport(models.Model):
    _inherit = "sale.report"

    amount_received = fields.Float(string='Amount Received', readonly=True)
    amount_to_invoice = fields.Float(string='Amount To Invoice', readonly=True)
    waiting_for_payment = fields.Float(string='Waiting for Payment', readonly=True)

    def _select_additional_fields(self):
        res = super()._select_additional_fields()
        res['amount_received'] = "CASE WHEN l.product_id IS NOT NULL THEN SUM(l.amount_received) ELSE 0 END"
        res['waiting_for_payment'] = "CASE WHEN l.product_id IS NOT NULL THEN SUM(l.waiting_for_payment) ELSE 0 END"
        res['amount_to_invoice'] = "CASE WHEN l.product_id IS NOT NULL THEN SUM(l.asa_amount_to_invoice) ELSE 0 END"
        return res



class AccountMove(models.Model):
    _inherit = 'account.move'
    amount_paid = fields.Float(string='amount paid', compute='_compute_amount_paid', store=True)
    amount_paid_cn = fields.Float(string='amount paid cn', compute='_compute_amount_paid', store=True)
    amount_dp = fields.Float(string='amount dp', compute='_compute_amount_dp', store=True)
    amount_dp2 = fields.Float(string='amount dp', compute='_compute_amount_dp', store=True)
    amount_dp_nopaid = fields.Float(string='amount dp', compute='_compute_amount_dp', store=True)
    amount_dp2_nopaid = fields.Float(string='amount dp', compute='_compute_amount_dp', store=True)
    amount_refund = fields.Float(string='amount refund', compute='_compute_amount_dp', store=True)
    amount_refund_nopaid = fields.Float(string='amount refund', compute='_compute_amount_dp', store=True)

    @api.depends('amount_residual', 'invoice_line_ids.price_subtotal', 'invoice_line_ids')
    def _compute_amount_paid(self):
        for move in self:
            if move.move_type == "out_refund":
                if move.payment_state in ['paid', 'in_payment', 'partial']:
                    move.amount_paid_cn = move.amount_total - move.amount_residual
            elif move.move_type == "out_invoice":
                if move.payment_state in ['paid', 'in_payment', 'partial']:
                    move.amount_paid = move.amount_total - move.amount_residual

    @api.depends('amount_residual', 'invoice_line_ids.price_subtotal', 'invoice_line_ids', 'payment_state', 'move_type')
    def _compute_amount_dp(self):
        for move in self:
            amount_dp = 0.0
            amount_dp2 = 0.0
            amount_dp_nopaid = 0.0
            amount_dp2_nopaid = 0.0
            amount_refund = 0.0
            amount_refund_nopaid = 0.0
            if move.move_type == "out_refund":
                for line in move.invoice_line_ids:
                    if line.product_id.name == "Down payment":
                        if move.payment_state in ['paid', 'in_payment']:
                            amount_refund = line.price_subtotal
                            amount_refund_nopaid = 0
                        else:
                            amount_refund = 0
                            amount_refund_nopaid = line.price_subtotal
            elif move.move_type == "out_invoice":
                for line in move.invoice_line_ids:
                    if line.product_id.name == "Down payment" and line.price_subtotal < 0:
                        if move.payment_state in ['paid', 'in_payment']:
                            amount_dp = line.price_subtotal
                            amount_dp_nopaid = 0
                        else:
                            amount_dp = 0
                            amount_dp_nopaid = line.price_subtotal
                    elif line.product_id.name == "Down payment" and line.price_subtotal > 0:
                        if move.payment_state in ['paid', 'in_payment']:
                            amount_dp2 = line.price_subtotal
                            amount_dp2_nopaid = 0
                        else:
                            amount_dp2 = 0
                            amount_dp2_nopaid = line.price_subtotal

            move.amount_dp = amount_dp
            move.amount_dp2 = amount_dp2
            move.amount_dp_nopaid = amount_dp_nopaid
            move.amount_dp2_nopaid = amount_dp2_nopaid
            move.amount_refund = amount_refund
            move.amount_refund_nopaid = amount_refund_nopaid


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    waiting_for_payment = fields.Float(string='Waiting for Payment', compute='_compute_waiting_for_payment_research', store=True)
    amount_received = fields.Float(string='Amount Received', compute='_compute_amount_received_research', store=True)
    asa_amount_to_invoice = fields.Float(string='Amount Received', compute='_compute_asa_amount_to_invoice', store=True)


    @api.depends('waiting_for_payment', 'amount_received', 'state', 'product_id', 'untaxed_amount_invoiced', 'qty_delivered', 'product_uom_qty', 'invoice_lines.move_id.amount_paid')
    def _compute_asa_amount_to_invoice(self):
        """ Total of remaining amount to invoice on the sale order line (taxes excl.) as
                total_sol - amount already invoiced
            where Total_sol depends on the invoice policy of the product.

            Note: Draft invoice are ignored on purpose, the 'to invoice' amount should
            come only from the SO lines.
        """
        for line in self:
            amount_to_invoice = 0.0
            if line.state in ['sale', 'done']:
                # Note: do not use price_subtotal field as it returns zero when the ordered quantity is
                # zero. It causes problem for expense line (e.i.: ordered qty = 0, deli qty = 4,
                # price_unit = 20 ; subtotal is zero), but when you can invoice the line, you see an
                # amount and not zero. Since we compute untaxed amount, we can use directly the price
                # reduce (to include discount) without using `compute_all()` method on taxes.
                price_subtotal = 0.0
                uom_qty_to_consider = line.qty_delivered if line.product_id.invoice_policy == 'delivery' else line.product_uom_qty
                price_reduce = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                price_subtotal = price_reduce * uom_qty_to_consider
                if len(line.tax_id.filtered(lambda tax: tax.price_include)) > 0:
                    # As included taxes are not excluded from the computed subtotal, `compute_all()` method
                    # has to be called to retrieve the subtotal without them.
                    # `price_reduce_taxexcl` cannot be used as it is computed from `price_subtotal` field. (see upper Note)
                    price_subtotal = line.tax_id.compute_all(
                        price_reduce,
                        currency=line.currency_id,
                        quantity=uom_qty_to_consider,
                        product=line.product_id,
                        partner=line.order_id.partner_shipping_id)['total_excluded']
                inv_lines = line._get_invoice_lines()
                if any(inv_lines.mapped(lambda l: l.discount != line.discount)):
                    # In case of re-invoicing with different discount we try to calculate manually the
                    # remaining amount to invoice
                    amount = 0
                    for l in inv_lines:
                        if len(l.tax_ids.filtered(lambda tax: tax.price_include)) > 0:
                            amount += l.tax_ids.compute_all(
                                l.currency_id._convert(l.price_unit, line.currency_id, line.company_id,
                                                       l.date or fields.Date.today(), round=False) * l.quantity)[
                                'total_excluded']
                        else:
                            amount += l.currency_id._convert(l.price_unit, line.currency_id, line.company_id,
                                                             l.date or fields.Date.today(), round=False) * l.quantity

                    amount_to_invoice = max(price_subtotal - amount, 0)
                else:
                    amount_to_invoice = line.price_subtotal - (line.waiting_for_payment + line.amount_received)

            line.asa_amount_to_invoice = amount_to_invoice

    @api.depends('amount_received', 'asa_amount_to_invoice', 'order_id', 'invoice_lines',
                 'invoice_lines.price_total', 'invoice_lines.move_id.state', 'invoice_lines.move_id.payment_state',
                 'invoice_lines.move_id.move_type', 'invoice_lines.move_id.amount_residual',
                 'invoice_lines.move_id.amount_paid')
    def _compute_waiting_for_payment_research(self):
        for line in self:
            amount_dp_nopaid = 0.0
            amount_dp_nopaid_dp = 0.0
            fixed_waiting_for_payment = 0.0
            amount_residual = 0.0
            for invoice_line in line._get_invoice_lines():
                if invoice_line.move_id.state != 'cancel':
                    if invoice_line.move_id.payment_state == "not_paid" or invoice_line.move_id.payment_state == "partial":
                        invoice_date = invoice_line.move_id.invoice_date or fields.Date.today()
                        amount_total = invoice_line.move_id.amount_untaxed
                        amount_dp_nopaid = invoice_line.move_id.amount_dp_nopaid + invoice_line.move_id.amount_dp2_nopaid - invoice_line.move_id.amount_refund_nopaid
                        amount_dp_nopaid_dp += invoice_line.move_id.amount_dp_nopaid + invoice_line.move_id.amount_dp2_nopaid - invoice_line.move_id.amount_refund_nopaid
                        amount_residual = invoice_line.move_id.amount_residual
                        check = self.env['account.move.line'].search(
                            [('move_id', '=', invoice_line.move_id.id), ('product_id.name', 'ilike', 'Down payment')])
                        if invoice_line.move_id.move_type == 'out_invoice':
                            waiting_for_payment = invoice_line.currency_id._convert(invoice_line.price_subtotal, line.currency_id,line.company_id, invoice_date)
                            if amount_total == 0:
                                fixed_waiting_for_payment += 0
                            else:
                                if check:
                                    dp_proportion = ( waiting_for_payment / (amount_total - invoice_line.move_id.amount_dp_nopaid) * invoice_line.move_id.amount_dp_nopaid)
                                    fixed_waiting_for_payment += (amount_residual - amount_dp_nopaid) * ((waiting_for_payment+dp_proportion) / (amount_total))
                                else:
                                    fixed_waiting_for_payment += (amount_residual) * ((waiting_for_payment) / (amount_total))

                        elif invoice_line.move_id.move_type == 'out_refund':
                            waiting_for_payment = invoice_line.currency_id._convert(invoice_line.price_subtotal,line.currency_id, line.company_id,invoice_date)
                            if amount_total == 0:
                                fixed_waiting_for_payment -= 0
                            else:
                                if check:
                                    dp_proportion = ( waiting_for_payment / (amount_total - invoice_line.move_id.amount_dp_nopaid) * invoice_line.move_id.amount_dp_nopaid)
                                    fixed_waiting_for_payment -= (amount_residual - amount_dp_nopaid) * ((waiting_for_payment + dp_proportion) / (amount_total))
                                else:
                                    fixed_waiting_for_payment -= (amount_residual) * ((waiting_for_payment) / (amount_total))

            if (amount_residual == 0 or line.amount_received == line.price_subtotal) and line.product_template_id.name != "Down payment":
                line.waiting_for_payment = 0
            elif line.product_template_id.name == "Down payment":
                line.waiting_for_payment = amount_dp_nopaid_dp
            else:
                line.waiting_for_payment = fixed_waiting_for_payment

    @api.depends('waiting_for_payment', 'asa_amount_to_invoice', 'order_id',
                 'invoice_lines', 'invoice_lines.price_total', 'invoice_lines.move_id.state',
                 'invoice_lines.move_id.payment_state', 'invoice_lines.move_id.move_type',
                 'invoice_lines.move_id.amount_residual', 'invoice_lines.move_id.amount_paid')
    def _compute_amount_received_research(self):
        for line in self:
            amount_dp_paid = 0.0
            amount_paid = 0.0
            fix_amount_received = 0.0
            for invoice_line in line._get_invoice_lines():
                if invoice_line.move_id.state != 'cancel':
                    if invoice_line.move_id.payment_state in ['paid', 'in_payment', 'partial']:
                        invoice_date = invoice_line.move_id.invoice_date or fields.Date.today()
                        amount_total = invoice_line.move_id.amount_untaxed
                        amount_paid = invoice_line.move_id.amount_paid
                        amount_paid_cn = invoice_line.move_id.amount_paid_cn
                        amount_dp_paid += invoice_line.move_id.amount_dp2 + invoice_line.move_id.amount_dp - invoice_line.move_id.amount_refund
                        check = self.env['account.move.line'].search([('move_id','=',invoice_line.move_id.id),('product_id.name', 'ilike', 'Down payment')])
                        if invoice_line.move_id.move_type == 'out_invoice':
                            amount_received = invoice_line.currency_id._convert(invoice_line.price_subtotal, line.currency_id,line.company_id, invoice_date)
                            if amount_total == 0:
                                fix_amount_received += 0
                            else:
                                if check:
                                    dp_proportion = (amount_received / (amount_total - invoice_line.move_id.amount_dp_nopaid) * invoice_line.move_id.amount_dp_nopaid)
                                    fix_amount_received += amount_paid * ((amount_received+dp_proportion) / (amount_total))
                                else:
                                    fix_amount_received += amount_paid * ((amount_received) / (amount_total))
                        elif invoice_line.move_id.move_type == 'out_refund':
                            amount_received = invoice_line.currency_id._convert(invoice_line.price_subtotal, line.currency_id,line.company_id, invoice_date)
                            if amount_total == 0:
                                fix_amount_received -= 0
                            else:
                                if check:
                                    dp_proportion = (amount_received / (amount_total - invoice_line.move_id.amount_dp_nopaid) * invoice_line.move_id.amount_dp_nopaid)
                                    fix_amount_received -= amount_paid_cn * ((amount_received+dp_proportion) / (amount_total))
                                else:
                                    fix_amount_received -= amount_paid_cn * ((amount_received) / (amount_total))

            if line.product_template_id.name == "Down payment":
                line.amount_received = amount_dp_paid
            elif amount_paid == 0 and line.product_template_id.name != "Down payment":
                line.amount_received = 0
            else:
                line.amount_received = fix_amount_received
