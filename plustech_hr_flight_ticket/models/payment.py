# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    vacation_ticket_id = fields.Many2one('hr.flight.ticket', string='Vacation Ticket')

    def action_post(self):
        result = super(AccountPayment, self).action_post()
        if self.vacation_ticket_id:
            self.vacation_ticket_id.write({'state': 'paid'})
        return result


