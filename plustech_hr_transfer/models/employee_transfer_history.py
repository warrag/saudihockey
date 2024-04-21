# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date


class EmployeeTransferHistory(models.Model):
    _name = "employee.transfer.history"
    _rec_name = 'employee_id'

    transfer_id = fields.Many2one('hr.employee.transfer', readonly=True)
    department_id = fields.Many2one('hr.department', string='Department', readonly=True)
    from_date = fields.Date(string='Date From', readonly=True)
    date_to = fields.Date(default=fields.Date.today(), string='Date To', readonly=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Cost Center', readonly=True)
    employee_id = fields.Many2one('hr.employee')
    manager_id = fields.Many2one('hr.employee', string='Manager', required=False)
    job_id = fields.Many2one('hr.job', string="New Job Position")
    new_department_id = fields.Many2one('hr.department', string='New Department Transfer',
                                        domain="[('id', '!=', department_id)]")
    state = fields.Selection(
        [('draft', 'Draft'), ('submit', 'Current Manager Approval'),
         ('new_manager_approval', 'New Manager Approval'),
         ('hr_approval', 'Waiting for HR Approval'), ('approve', 'Approved'),
         ('refuse', 'Refused')],
        string="State", default='draft', tracking=True)


class HREmployee(models.Model):
    _inherit = "hr.employee"

    transfer_ids = fields.One2many(
        comodel_name='employee.transfer.history',
        inverse_name='employee_id',
        string='Transfer ids',
        required=False, readonly=True)

    check_department = fields.Boolean(string='Check Department')

    @api.model
    def create(self, vals):
        if 'department_id' in vals and vals['department_id']:
            vals['check_department'] = True
        return super(HREmployee, self).create(vals)

    def write(self, vals):
        if 'department_id' in vals and vals['department_id']:
            vals['check_department'] = True
        return super(HREmployee, self).write(vals)

    def open_transfer_history(self):
        action = self.env.ref('hr_department_transfer.action_employee_transfer_history').read()[0]
        action['domain'] = [('employee_id', 'in', self.ids), ('state', '=', 'approve')]
        return action
