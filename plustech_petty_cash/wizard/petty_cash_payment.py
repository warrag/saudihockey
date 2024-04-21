# -*- coding: utf-8 -*-


from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)


class AccountTransferWizard(models.TransientModel):
    _name = 'account.transfer.wizard'

    def _get_default_transfer_account_id(self):
        return self.env.user.company_id.petty_transfer_account_id.id

    def _get_default_payment_journal_id(self):
        return self.env.user.company_id.payment_journal_id.id

    def _get_default_petty_analytic_account_id(self):
        return self.env.user.company_id.petty_analytic_account_id.id

    res_id = fields.Many2one('account.journal.transfer')
    payment_journal_id = fields.Many2one(
        'account.journal', default=_get_default_payment_journal_id)
    petty_analytic_account_id = fields.Many2one(
        'account.analytic.account', string='Analytic Account', default=_get_default_petty_analytic_account_id)
    petty_transfer_account_id = fields.Many2one(
        comodel_name='account.account', string='Internal Transfer Account',  default=_get_default_transfer_account_id)

    def action_wizard_approve(self):
        amount = self.res_id.amount
        move_line_name = 'Petty Cash Transfer For '+self.res_id.petty_user_id.employee_id.name or ''
        credit_vals= {
            'name': move_line_name,
            'account_id': self.payment_journal_id.default_account_id.id,
            'date': datetime.today().date(),
            'currency_id': self.env.user.company_id.currency_id.id,
            'credit': amount > 0.0 and amount or 0.0,
            'debit': amount < 0.0 and -amount or 0.0,
            'analytic_account_id': self.petty_analytic_account_id.id,
        }
        debit_vals = {
            'name': move_line_name,
            'account_id': self.petty_transfer_account_id.id,
            'currency_id': self.env.user.company_id.currency_id.id,
            'date': datetime.today().date(),
            'credit': amount < 0.0 and -amount or 0.0,
            'debit': amount > 0.0 and amount or 0.0,
            'analytic_account_id': self.petty_analytic_account_id.id,
        }
        vals = {
            'ref': 'Petty Cash' + ' ' + self.res_id.name,
            'journal_id': self.payment_journal_id.id,
            'is_petty_cash_transfer': True,
            'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
        }
        move = self.env['account.move'].sudo().create(vals)
        move.action_post()
        self.res_id.transfer_move_ids = [(4, move.id)]
        self.res_id.state = 'finance'
