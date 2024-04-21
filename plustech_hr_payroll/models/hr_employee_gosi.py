# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class HrEmployeeGosi(models.Model):
    _name = 'hr.employee.gosi'
    _description = 'Employee Gosi'

    @api.model
    def _countries_domain(self):
        countries = self.env['hr.employee'].search([('active', '=', True)]).mapped('country_id')
        domain = [('id', 'in', countries.ids)]
        return domain

    name = fields.Char(string='Name', required=1, translate=True)
    gosi_type = fields.Selection([('company', 'Company'), ('employee', 'Employee')])
    country_ids = fields.Many2many('res.country', string='Allowed Nationalities', domain=_countries_domain, required=1)
    percentage = fields.Float(string='Percentage')
    is_active = fields.Boolean(string='Active')


class GosiDailyContribution(models.Model):
    _name = 'gosi.daily.contribution'
    _description = 'Gosi Daily Contribution'

    month_char = fields.Char(string='Months Name')
    sequence = fields.Integer(string='Month')
    days = fields.Char(string='Month Days')
    gosi_company_daily = fields.Float(string='Daily Company Deduction')
    gosi_employee_daily = fields.Float(string='Daily Employee Deduction')
    contract_id = fields.Many2one('hr.contract')
    currency_id = fields.Many2one('res.currency', related='contract_id.currency_id')

