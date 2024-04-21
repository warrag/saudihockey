# -*- coding: utf-8 -*-

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    employee_cost_center = fields.Selection(string='Employee Cost Center', selection=[
        ('department', 'By Department'),
        ('location', 'By Work Location'),
        ('attendance', 'By Attendance Location')
    ], default="department")
