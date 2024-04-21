# -*- coding: utf-8 -*-

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    def _domain_product_company(self):
        company = self.env.company
        return ['|', ('company_id', '=', False), ('company_id', '=', company.id),('detailed_type', '=', 'service')]

    def _domain_company(self):
        company = self.env.company
        return ['|', ('company_id', '=', False), ('company_id', '=', company.id)]

    overtime_product_id = fields.Many2one('product.product', string='Overtime Expense Product',
                                                      domain=_domain_product_company)
    overtime_analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account',
                                                     domain=_domain_company)
    overtime_payment = fields.Selection([('payroll', 'Payroll'), ('finance', 'Finance')],
                                        string='Overtime Payment Options', default='payroll')
    overtime_cal_days = fields.Integer(string='Calculation Days', default=22)
    overtime_cal_hours = fields.Integer(string='Calculation Hours', default=176)
