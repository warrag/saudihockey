from odoo import fields, models, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _get_default_petty(self):
        petty_cash_ids = self.env['account.journal.transfer'].sudo().search([
            ('user_id', '=', self.env.user.id),
            ('state', '=', 'running'), ('remaining_amount', '>', 0),
        ], order='id asc').ids
        return petty_cash_ids if self.env.context.get('default_petty') else False

    petty = fields.Boolean('Petty')
    petty_ids = fields.Many2many(comodel_name='account.journal.transfer', default=_get_default_petty)
    state = fields.Selection(selection_add=[('confirm', 'Confirmed')], ondelete={'confirm': 'set default'})
    petty_payment_id = fields.Many2one('account.payment')

    is_petty_cash_transfer = fields.Boolean('is_petty_cash_transfer')
    is_petty_cash_payment = fields.Boolean('is_petty_cash_payment')

    @api.onchange('petty')
    def change_petty(self):
        self.journal_id = self.env.user.company_id.purchase_journal_id.id

    def action_petty_confirm(self):
        self.state = 'confirm'

    def action_post(self):
        res = super(AccountMove, self).action_post()
        if self.petty_ids and not self.env.context.get('petty_cash_reconcile'):
            move_lines = self._prepare_move_lines()
            move_vals = {'ref': 'Petty Cash Bill %s Reconcile' % self.name,
                         'journal_id': self.company_id.petty_journal_id.id, 'move_type': 'entry',
                         'is_petty_cash_payment': True,
                         'date': fields.Date.today(), 'line_ids': move_lines}
            move = self.env['account.move'].with_context(petty_cash_reconcile=True).create(move_vals)
            move.post()
            for invoice in self:
                for line in move.line_ids:
                    invoice.js_assign_outstanding_line(line.id)
        return res

    def _prepare_move_lines(self):
        amount = 0.0
        to_reconcile_lines = []
        for petty in self.petty_ids.sorted(lambda line: line.id, reverse=False):
            if amount < self.amount_residual:
                if (amount+petty.remaining_amount) <= self.amount_residual:
                    to_reconcile_lines.append({
                        'amount': petty.remaining_amount,
                        'petty_cash_id': petty.id,
                        'move_id': self.id,
                        'reconciliation_date': self.invoice_date
                    })
                else:
                    to_reconcile_lines.append({
                        'amount': (self.amount_residual - amount),
                        'petty_cash_id': petty.id,
                        'move_id': self.id,
                        'reconciliation_date': self.invoice_date
                    })
                amount += petty.remaining_amount
            if amount >= self.amount_residual:
                amount = self.amount_residual
                break
        self.env['petty_cash.reconcile.bill'].create(to_reconcile_lines)
        line_ids = []
        move_line_name = 'Petty Cash Reconcile For ' + self.petty_ids[0].petty_user_id.employee_id.name or ''
        credit_vals = {
            'name': move_line_name,
            'account_id': self.petty_ids[0].petty_user_id.employee_id.address_home_id.property_account_receivable_id.id,
            'credit': amount > 0.0 and amount or 0.0,
            'debit': amount < 0.0 and -amount or 0.0,
            'analytic_account_id': self.company_id.petty_analytic_account_id.id,
            'partner_id': self.petty_ids[0].petty_user_id.employee_id.address_home_id.id,
        }
        line_ids.append((0, 0, credit_vals))
        debit_vals = {
            'name': move_line_name,
            'account_id': self.partner_id.property_account_payable_id.id,
            'credit': amount < 0.0 and -amount or 0.0,
            'debit': amount > 0.0 and amount or 0.0,
            'analytic_account_id': self.company_id.petty_analytic_account_id.id,
            'partner_id': self.partner_id.id,
        }
        line_ids.append((0, 0, debit_vals))
        return line_ids


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.onchange('product_id')
    def change_product_get_domain2(self):
        if self.move_id.petty == True:
            product_ids = self.env['product.product'].search([
                ('expense_ok', '=', True),
                ('purchase_ok', '=', True),
                ('detailed_type', '=', 'service'),
            ])
            return {'domain': {'product_id': [('id', 'in', product_ids.ids)]}}
