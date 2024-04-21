# -*- coding: utf-8 -*-

from odoo import models, fields


class HrWorkLocation(models.Model):
    _inherit = "hr.work.location"

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')


