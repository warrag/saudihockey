# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    deputation_id = fields.Many2one('hr.deputation', string='Deputation', copy=False, help="deputation where the move line come from")

    def reconcile(self):
        # OVERRIDE
        res = super().reconcile()
        # Do not consider deputation if account_move_id is False, it means it has been just canceled
        not_paid_deputation = self.deputation_id.filtered(lambda deputation: deputation.account_move_id)
        paid_deputation = not_paid_deputation.filtered(lambda deputation: deputation.currency_id.is_zero(deputation.amount_residual))
        paid_deputation.write({'state': 'paid'})
        # if paid_deputation.state == 'paid':
        #     activity_type = self.env.ref('plustech_hr_deputations.mail_act_deputation_approval')
        #     domain = [
        #         ('res_model', '=', 'hr.deputation'),
        #         ('res_id', 'in', paid_deputation.ids),
        #         ('activity_type_id', '=', activity_type.id),
        #         ('user_id', '=', self.env.user.id)
        #     ]
        #     activities = self.env['mail.activity'].search(domain)
        #     activities.action_feedback()
        return res

