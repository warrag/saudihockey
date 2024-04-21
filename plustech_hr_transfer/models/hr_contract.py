# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HRContract(models.Model):
    _inherit = 'hr.contract'

    department_id = fields.Many2one('hr.department', string='Department', readonly=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')

    @api.onchange('department_id')
    def onchange_department_id(self):
        if self.department_id:
            self.analytic_account_id = self.department_id.analytic_account_id

    @api.model
    def create(self, vals):
        if vals.get('department_id'):
            department = self.env['hr.department'].browse(vals['department_id'])
            vals['analytic_account_id'] = department.analytic_account_id.id
        return super(HRContract, self).create(vals)
