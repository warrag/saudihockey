# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'
    
    salary_structure_id = fields.Many2one('hr.payroll.structure', string='End of service salary structure')
    month_type = fields.Selection(string='Month Type',selection=[
        ('0', 'Month According To user Need'),
        ('1', 'Month According to the actual date')
    ],default="1", required=1 )
    days_of_month = fields.Integer("Days Of Month", default="30")

    @api.onchange('month_type')
    def change_month_type(self):
        for rec in self:
            rec.days_of_month = 30
