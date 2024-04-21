# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    overtime_id = fields.Many2one('hr.overtime', string='Overtime', copy=False, help="overtime where the move line come from")

    def reconcile(self):
        # OVERRIDE
        res = super().reconcile()
        # Do not consider overtime if account_move_id is False, it means it has been just canceled
        not_paid_overtime = self.overtime_id.filtered(lambda ovt: ovt.account_move_id)
        not_paid_overtime = not_paid_overtime.filtered(lambda overtime: overtime.currency_id.is_zero(overtime.amount_residual))
        not_paid_overtime.write({'state': 'paid'})
        return res

