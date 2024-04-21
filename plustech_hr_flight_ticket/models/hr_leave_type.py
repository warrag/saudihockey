# -*- coding: utf-8 -*-

from odoo import models, fields


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    need_ticket = fields.Boolean(string='Employee Can Request Ticket?')
    min_days_for_ticket = fields.Integer(string='Minimum Leave Days For Ticket?')
    ticket_except_nationality_ids = fields.Many2many('res.country', string='Except Nationalities')
