# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    eos_id = fields.Many2one('end.of.service.reward', string='EOS Request')

    def action_post(self):
        result = super(AccountPayment, self).action_post()
        if self.eos_id:
            self.eos_id.write({'state':'paid'})
        return result


