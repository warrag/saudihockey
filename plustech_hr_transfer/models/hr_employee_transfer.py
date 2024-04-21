# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date


class HrEmployeeTransfer(models.Model):
    _name = "hr.employee.transfer"
    _rec_name = 'employee_id'
    _inherit = "mail.thread"

    employee_id = fields.Many2one('hr.employee', string="Employee")
    employee_number = fields.Char(related="employee_id.employee_number", string="Employee Number")
    department_id = fields.Many2one('hr.department', string='Department', readonly=True)
    manager_id = fields.Many2one('hr.employee', string='Manager', readonly=True)
    job_id = fields.Many2one('hr.job', string='Job Position', readonly=True)
    new_department_id = fields.Many2one('hr.department', string='Department Transfer',
                                        domain="[('id', '!=', department_id)]")
    new_job_position = fields.Many2one('hr.job', string="New Job Position")
    new_manager_id = fields.Many2one('hr.employee', string='New Manager')
    transfer_type = fields.Selection([('department', 'Department'), ('location', 'Work Location')],
                                     string="Transfer Type")
    previous_location_id = fields.Many2one('hr.work.location', string="Previous Work Location")
    new_location_id = fields.Many2one('hr.work.location', string="Transfer Work Location",
                                      domain="[('id', '!=', previous_location_id)]")
    state = fields.Selection(
        [('draft', 'Draft'), ('submit', 'Current Manager Approval'),
         ('new_manager_approval', 'New Manager Approval'),
         ('hr_approval', 'Waiting for HR Approval'), ('approve', 'Approved'),
         ('refuse', 'Refused')],
        string="State", default='draft', tracking=True)
    request_date = fields.Date(default=fields.Date.today(), string='Date From')
    message_follower_ids = fields.Many2many('res.partner', string='Followers')
    message_ids = fields.One2many('mail.message', 'res_id', string='Messages',
                                  domain=lambda self: [('message_type', '!=', 'user_notification')], auto_join=True)
    date_to = fields.Date(default=fields.Date.today(), string='Date To')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Cost Center')
    current_manager = fields.Boolean(compute='_compute_current_manager', string='Current Manager', store=True)
    new_manager = fields.Boolean(compute='_compute_new_manager', string='New manager approval', store=True)

    @api.onchange('new_department_id', 'new_location_id')
    def change_analytic_account(self):
        if self.transfer_type == 'location':
            self.analytic_account_id = self.new_department_id.analytic_account_id
        else:
            self.analytic_account_id = self.new_location_id.analytic_account_id

    @api.depends('new_department_id.manager_id', 'new_department_id')
    def _compute_new_manager(self):
        for record in self:
            if record.new_department_id.manager_id.user_id.id == self.env.user.id:
                record.new_manager = True
            else:
                record.new_manager = False

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if self.employee_id:
            self.previous_location_id = self.employee_id.work_location_id
            self.department_id = self.employee_id.department_id
            self.manager_id = self.employee_id.parent_id
            self.job_id = self.employee_id.job_id

    @api.depends('department_id.manager_id', 'department_id')
    def _compute_current_manager(self):
        for record in self:
            if record.department_id.manager_id.user_id.id == self.env.user.id:
                record.current_manager = True
            else:
                record.current_manager = False

    @api.constrains('new_department_id')
    def _check_new_department_id(self):
        for record in self:
            if not record.new_department_id:
                raise ValidationError("Please fill in the required field: Department Transfer")

    def submit_btn(self):
        self.state = 'submit'

    def approve_btn(self):
        self.state = 'new_manager_approval'

    def new_manager_approve_btn(self):
        self.state = 'hr_approval'

    def hr_approve_btn(self):
        self.state = 'approve'
        vals = {
            'department_id': self.department_id.id,
            'new_department_id': self.new_department_id.id,
            'manager_id': self.new_manager_id.id,
            'employee_id': self.employee_id.id,
            'date_to': self.date_to,
            'from_date': self.request_date,
            'analytic_account_id': self.new_department_id.analytic_account_id.id,
            'state': self.state,
        }
        print(vals)
        self.env['employee.transfer.history'].create(vals)

        contract_ids = self.employee_id.contract_ids.filtered(
            lambda c: c.state in ('open', 'pending', 'close')
        )
        contract_ids.write({'department_id': self.new_department_id.id,
                            'analytic_account_id': self.new_department_id.analytic_account_id.id})

        self.employee_id.write({'department_id': self.new_department_id.id})

    def refuse_btn(self):
        self.state = 'refuse'
