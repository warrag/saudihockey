# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class WorkingSchedule(models.Model):
    _inherit = 'resource.calendar'

    check_in_early = fields.Selection([('yes', 'Yes'), ('no', 'No')], default='yes',
                                      string='Auto Overtime(Check-In Early)', required=True)
    min_ot_check_in = fields.Integer(string='Min minutes OT(Check-In Early)', default=60, required=True)
    check_out_delay = fields.Selection([('yes', 'Yes'), ('no', 'No')], default='yes',
                                       string='Auto Overtime(Check-Out Delay)', required=True)
    min_ot_check_out = fields.Integer(string='Min minutes OT(Check-Out Delay)', default=60, required=True)
    ot_working_day = fields.Float(string='1 minute working day overtime =', default=1.5)
    ot_holiday = fields.Float(string='1 minute holiday overtime =', default=2)
    