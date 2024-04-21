# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    overtime_product_id = fields.Many2one('product.product', string='Overtime Expense Product',
                                                    related="company_id.overtime_product_id",
                                                    domain=[('detailed_type', '=', 'service')], readonly=False)
    overtime_analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account',
                                                   readonly=False,
                                                   related="company_id.overtime_analytic_account_id",
                                                   )
    overtime_payment = fields.Selection([('payroll', 'Payroll'), ('finance', 'Finance')],
                                        string='Overtime Payment Options', readonly=False,
                                        related="company_id.overtime_payment", default='payroll')
    overtime_cal_days = fields.Integer(string='Overtime Calculation Days',  related="company_id.overtime_cal_days",
                                       default=22, readonly=False)
    overtime_cal_hours = fields.Integer(string='Overtime Calculation Hours', related="company_id.overtime_cal_hours",
                                        default=176, readonly=False)
