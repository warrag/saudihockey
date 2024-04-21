# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools import float_round


class HrVacationEntitlement(models.Model):
    _name = 'hr.vacation.entitlement'
    _description = 'Vacation Entitlement'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char()
    employee_id = fields.Many2one(
        'hr.employee', string='Employee', required=True, help="Employee")
    leave_id = fields.Many2one(
        'hr.leave', string='Leave', domain="[('employee_id','=',employee_id)]", required=True,
        help="Employee Validated Leave")
    date = fields.Date(string='Date', required=True,
                       default=fields.Date.today())
    date_from = fields.Date(string='From', required=True,
                            related='leave_id.request_date_from', help="Start date")
    date_to = fields.Date(string='To', required=True,
                          related='leave_id.request_date_to', help="End date")
    duration = fields.Float(
        string='Duration', related='leave_id.number_of_days', required=False, help="Leave Duration")
    state = fields.Selection([('draft', 'New'), ('submit', 'Submitted'), ('confirmed', 'Confirmed'),
                              ('validate', 'Validated'), ('completed', 'Completed'), ('cancel', 'Canceled')],
                             string='Status', default='draft', tracking=True)
    working_days = fields.Float(string='Working Days', tracking=True, compute='_compute_working_days', store=True)
    payslips_amount = fields.Float(compute='_compute_payslips_amount')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)
    payslip_date_from = fields.Date(string='Payslip From Date')
    payslip_date_to = fields.Date(string='Payslip Date To')
    vacation_salary_in_advance = fields.Boolean(string='Vacation Salary in Advance')
    leave_salary = fields.Float(string='Leave Salary', compute='_compute_leave_salary', store=True)

    def _compute_payslips_amount(self):
        for record in self:
            payslip = self.env['hr.payslip'].search([('vacation_entitlement_id', '=', self.id)]).mapped('net_wage')
            record.payslips_amount = sum(payslip)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            seq_date = None
            if 'date' in vals:
                seq_date = fields.Datetime.context_timestamp(
                    self, fields.Datetime.to_datetime(vals['date']))
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'vacation.entitlement', sequence_date=seq_date) or _('New')
        result = super(HrVacationEntitlement, self).create(vals)
        return result

    def action_submit(self):
        for record in self:
            record.write({'state': 'submit'})
        return True

    def action_confirm(self):
        for record in self:
            record.write({'state': 'confirmed'})
        return True

    def action_validate(self):
        for record in self:
            record.write({'state': 'validate'})
        return True

    def action_cancel(self):
        for record in self:
            record.write({'state': 'cancel'})
        return True

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if not self.payslip_date_from:
            payslip = self.env['hr.payslip'].search([('employee_id', '=', self.employee_id.id), ('state', '=', 'paid')])
            if payslip:
                to_date = payslip.mapped('date_to')
                latest = max(to_date)
                self.payslip_date_from = latest

    # @api.onchange('leave_id')
    # def _onchange_leave_id(self):
    #     if not self.paid_days:
    #         self.paid_days - self.duration

    @api.depends('payslip_date_from', 'payslip_date_to')
    def _compute_working_days(self):
        if self.payslip_date_from and self.payslip_date_to:
            self.working_days = (self.payslip_date_to - self.payslip_date_from).days + 1
        else:
            self.working_days = 0

    @api.depends('vacation_salary_in_advance', 'leave_id')
    def _compute_leave_salary(self):
        for record in self:
            contract_id = record.employee_id.contract_id
            amount = 0.0
            if contract_id:
                allowance_ids = contract_id.allowance_ids.filtered(lambda line: line.leave_compensation)
                allowances = [contract_id.get_allowance(line.allowance_type.code) for line in allowance_ids]
                month_days = contract_id.company_id.days_per_year / 12
                amount = (contract_id.wage + sum(allowances)) / month_days
            record.leave_salary = amount * record.duration

    def create_payslip(self):
        action = self.env["ir.actions.actions"]._for_xml_id(
            'hr_payroll.action_view_hr_payslip_month_form')
        date_to = self.date_from
        action.update({'view_mode': 'form',
                       'views': [(False, 'form')],
                       'context': {
                           'default_employee_id': self.employee_id.id,
                           'default_contract_id': self.employee_id.contract_id.id,
                           'default_date_to': date_to,
                           'default_vacation_entitlement_id': self.id,
                           'default_payslip_type': 'leave_salary'
                       }
                       })
        return action

    def action_open_payslips(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("hr_payroll.action_view_hr_payslip_month_form")
        action.update({'domain': [('vacation_entitlement_id', '=', self.id)]})
        return action


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    has_entitlement = fields.Boolean(compute='_compute_entitlement', store=True)

    def _compute_entitlement(self):
        for leave in self:
            entitlements = self.env['hr.vacation.entitlement'].search([('leave_id', '=', leave.id)])
            if entitlements:
                leave.has_entitlement = True
            else:
                leave.has_entitlement = False
