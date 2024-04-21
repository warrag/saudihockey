# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HrDepartment(models.Model):
    _inherit = "hr.department"

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')


