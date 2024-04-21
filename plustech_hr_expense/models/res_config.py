# -*- coding: utf-8 -*-

from odoo import fields, models


class ConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    employee_cost_center = fields.Selection(string='Employee Cost Center', related='company_id.employee_cost_center',
                                            readonly=False, required=1, )
