# -*- coding: utf-8 -*-

from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    insurance_ids = fields.One2many(comodel_name='insurance.request', inverse_name='employee_id', string='')
    insurance_class = fields.Char(string='Insurance Class')


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    insurance_class = fields.Char(string='Insurance Class')
    
