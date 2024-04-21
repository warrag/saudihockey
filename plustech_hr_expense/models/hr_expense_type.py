# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta


class HrExpenseType(models.Model):
    _name = 'hr.expense.type'
    _description = 'Employee Expense Type'

    name = fields.Char(string='Name', translate=True, required=True)
    export_as = fields.Selection([('bill', 'Bill'), ('deferred', 'Deferred')],
                                 string='Export AS', required=True)
    product_id = fields.Many2one('product.product', string="Expense Product",
                                 domain="[('detailed_type', '=', 'service')]")
    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account")
    analytic_tag_id = fields.Many2one('account.analytic.tag', string="Analytic Tag")
