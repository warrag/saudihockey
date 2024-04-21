# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrPayslipCorrection(models.Model):
    _name = 'hr.payslip.correction'
    _description = 'Hr Payslip Correction'
    _rec_name = 'employee_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _get_current_employee(self):
        employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
        if employee_id:
            return employee_id

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, default=_get_current_employee)
    payslip_id = fields.Many2one('hr.payslip', string='Payslip',
                                  domain="[('employee_id', '=', employee_id)]")
    employee_note = fields.Text(string="Employee Note")
    manager_note = fields.Text(string="Manager Note")
    hr_note = fields.Text(string="Hr Note")
    reason = fields.Text(string="Reason")
    result = fields.Text(string="Result")
    is_hidden = fields.Boolean()
    state = fields.Selection([
        ('draft', 'Submitted'),
        ('manager_approved', 'Manager Approved'),
        ('hr_approved', 'Hr Approve'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
    ], string='Status', readonly=True, tracking=True, copy=False, default='draft')

    salary_computation_ids = fields.One2many('hr.payslip.line.correction', 'payslip_correction_id',
                                             forc_save=True)
    worked_days_ids = fields.One2many('hr.payslip.worked.correction', 'payslip_correction_id',
                                      forc_save=True, store=True,)
    payslip_input_ids = fields.One2many('hr.payslip.input.correction', 'payslip_correction_id',
                                        forc_save=True, store=True, readonly=True)

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = {} if default is None else default.copy()
        default.update({
            'is_hidden': False,
            'employee_note': False,
            'manager_note': False,
            'hr_note': False,
            'reason': False,
            'result': False
        })
        return super(HrPayslipCorrection, self).copy(default=default)

    def write(self, values):
        parent_id = self.employee_id.parent_id
        current_user_id = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)]).id
        if 'manager_note' in values:
            if parent_id:
                if parent_id.id != current_user_id:
                    raise UserError(_("You aren't The Manager Of That Employee To Change The Note"))
        if 'state' in values:
            if values['state'] == 'manager_approved':
                if parent_id:
                    if parent_id.id != current_user_id:
                        raise UserError(_("You aren't The Manager Of That Employee To Change The State"))
            if values['state'] == 'hr_approved':
                if not self.env.user.has_group('hr_payslip_correction.group_hr_approve'):
                    raise UserError(_("You aren't The Manager Of That Employee To Change The State"))
            if values['state'] == 'cancel':
                if not self.env.user.has_group('hr_payslip_correction.group_cancel'):
                    raise UserError(_("You aren't Allowed To Change State To Cancel"))
            if values['state'] == 'done':
                if not self.env.user.has_group('hr_payslip_correction.group_generate_payslip'):
                    raise UserError(_("You aren't Allowed To Change State To Done"))
        if 'hr_note' in values:
            if not self.env.user.has_group('hr_payslip_correction.group_hr_approve'):
                raise UserError(_("You aren't The HR Manager To Change The Note"))
        res = super(HrPayslipCorrection, self).write(values)
        return res

    @api.onchange('employee_id')
    def get_related_employee(self):
        current_user_id = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)]).id
        employee_ids = self.env['hr.employee'].search([('parent_id.id', '=', current_user_id)])
        employees = []
        for employee in employee_ids:
            employees.append(employee.id)
        domain = {'employee_id': [('id', 'in', employees)]}
        return {'domain': domain}

    @api.onchange('payslip_id')
    def get_salary_computation_line(self):
        self.salary_computation_ids = False
        self.worked_days_ids = False
        self.payslip_input_ids = False
        if self.payslip_id:
            payslip_obj = self.env['hr.payslip.line'].search([('slip_id.id', '=', self.payslip_id.id)])
            work_days_obj = self.env['hr.payslip.worked_days'].search([('payslip_id.id', '=', self.payslip_id.id)])
            input_obj = self.env['hr.payslip.input'].search([('payslip_id.id', '=', self.payslip_id.id)])
            if payslip_obj:
                for line in payslip_obj:
                    self.salary_computation_ids.new({
                        'payslip_correction_id': self.id,
                        'name': line.name,
                        'amount': line.amount,
                        'total': line.total,
                    })
            if work_days_obj:
                for d in work_days_obj:
                    self.worked_days_ids.new({
                        'payslip_correction_id': self.id,
                        'work_entry_type_id': d.work_entry_type_id.id,
                        'name': d.name,
                        'number_of_days': d.number_of_days,
                        'number_of_hours': d.number_of_hours,
                        'amount': d.amount,
                    })
            if input_obj:
                for i in input_obj:
                    self.payslip_input_ids.new({
                        'payslip_correction_id': self.id,
                        'input_type_id': i.input_type_id.id,
                        'amount': i.amount,
                    })

    def action_manager_approve(self):
        for record in self:
            if not record.manager_note:
                raise UserError(_("Please Add Your Note"))
            record.state = 'manager_approved'

    def action_hr_approve(self):
        for record in self:
            if not record.hr_note:
                raise UserError(_("Please Add Your Note"))
            record.is_hidden = True
            record.state = 'hr_approved'

    def action_cancel(self):
        for record in self:
            if not record.reason:
                raise UserError(_("Please Add The Reason"))
            record.is_hidden = True
            record.state = 'cancel'

    def action_generate_payslip(self):
        for record in self:
            payslip_line_obj = self.env['hr.payslip.line']
            worked_days_obj = self.env['hr.payslip.worked_days']
            input_obj = self.env['hr.payslip.input']
            payslip_obj = self.env['hr.payslip'].create({
                'employee_id': record.employee_id.id,
                'date_from': record.payslip_id.date_from,
                'date_to': record.payslip_id.date_to,
                'contract_id': record.payslip_id.contract_id.id,
                'struct_id': record.payslip_id.struct_id.id,
                'name': record.payslip_id.name,
            })
            if record.payslip_id:
                for line in record.payslip_id.line_ids:
                    payslip_line_obj.create({
                        'slip_id': payslip_obj.id,
                        'name': line.name,
                        'amount': line.amount,
                        'total': line.total,
                        'code': line.code,
                        'salary_rule_id': line.salary_rule_id.id,
                    })
            if record.worked_days_ids:
                for work in record.worked_days_ids:
                    worked_days_obj.create({
                        'payslip_id': payslip_obj.id,
                        'amount': work.amount,
                        'work_entry_type_id': work.work_entry_type_id.id,
                        'name': work.name,
                        'number_of_days': work.number_of_days,
                        'number_of_hours': work.number_of_hours,
                    })
            if record.payslip_input_ids:
                for in_put in record.payslip_input_ids:
                    input_obj.create({
                        'payslip_id': payslip_obj.id,
                        'amount': in_put.amount,
                        'input_type_id': in_put.input_type_id.id,
                    })
            payslip_obj.payslip_correction_id = record.id
            x = str(record.result) if record.result else False
            record.result = x + " " + self.payslip_id.name if x else self.payslip_id.name
            record.state = 'done'


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    payslip_correction_id = fields.Many2one('hr.payslip.correction')


class HrPayslipLine(models.Model):
    _name = 'hr.payslip.line.correction'
    payslip_correction_id = fields.Many2one('hr.payslip.correction')
    name = fields.Char()
    amount = fields.Float()
    total = fields.Float()


class HrPayslipWorkedDays(models.Model):
    _name = 'hr.payslip.worked.correction'
    payslip_correction_id = fields.Many2one('hr.payslip.correction')
    work_entry_type_id = fields.Many2one('hr.work.entry.type')
    name = fields.Char()
    number_of_days = fields.Float()
    number_of_hours = fields.Float()
    amount = fields.Float()


class HrPayslipInput(models.Model):
    _name = 'hr.payslip.input.correction'
    payslip_correction_id = fields.Many2one('hr.payslip.correction')
    input_type_id = fields.Many2one('hr.payslip.input.type')
    amount = fields.Float()
