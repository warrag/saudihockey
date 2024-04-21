# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    
    salary_structure_id = fields.Many2one('hr.payroll.structure', string='End of service salary structure',
                                          related='company_id.salary_structure_id', readonly=False)
    month_type = fields.Selection(string='Month Type',related='company_id.month_type', readonly=False, required=1,  )
    days_of_month = fields.Integer("Days Of Month",related='company_id.days_of_month', readonly=False)
