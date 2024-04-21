# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta
import math
from calendar import monthrange
from odoo.addons.plustech_hr_employee.models.hr_employee import is_leap_year


def relativeDelta(enddate, startdate):
    if not startdate or not enddate:
        return relativedelta()
    startdate = fields.Datetime.from_string(startdate)
    enddate = fields.Datetime.from_string(enddate) + relativedelta(days=1)
    return relativedelta(enddate, startdate)


def delta_desc(delta):
    res = []
    if delta.years:
        res.append('%s Years' % delta.years)
    if delta.months:
        res.append('%s Months' % delta.months)
    if delta.days:
        res.append('%s Days' % delta.days)
    return ', '.join(res)


class EndOfServiceReward(models.Model):
    _name = 'end.of.service.reward'
    _description = 'End of Service Reward'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _check_company_auto = True

    name = fields.Char(string='Number#', default='New')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, index=True, tracking=True)
    employee_number = fields.Char(related='employee_id.employee_number', string='Employee Number')
    contract_id = fields.Many2one('hr.contract', string='Contract', domain="[('employee_id', '=', employee_id)]",
                                  tracking=True, copy=False, related='employee_id.contract_id')
    join_date = fields.Date(string="Join Date", related='employee_id.join_date', tracking=True)
    last_work_date = fields.Date(tracking=True)
    request_date = fields.Date(string='Date', default=fields.Date.today())
    service_years = fields.Integer(string='Period in years')
    service_months = fields.Integer(string='Period in months')
    service_days = fields.Integer(string='Period in days')
    total_service_year = fields.Float('Total Service Years', compute='_calc_service_year', store=True)
    number_of_days_from_join_date = fields.Integer(string="Days From Join Date",
                                                   compute='_compute_number_of_days_from_join_date', tracking=True)
    remaining_leaves = fields.Float(compute='_compute_remaining_leave_balance', store=True)
    leave_balance_reward = fields.Monetary(string='Leave Balance Reward')
    net_period_reward = fields.Monetary(string='EOS Reward')
    total_reward = fields.Monetary(string='Total Reward', compute='_compute_total_reward', store=True)
    deserving = fields.Monetary(string="Deserving")
    final_deserving = fields.Monetary(string="Total Deserved Amount", compute='_compute_final_deserving')
    state = fields.Selection([
        ('draft', 'Draft'), ('submit', 'Submitted'),
        ('hro', 'HRO'), ('hrm', 'HRM'), ('paid', 'Paid')
    ], string='Status', readonly=True, tracking=True, copy=False, default='draft')
    reason_id = fields.Many2one(comodel_name='end.service.reason',
                                string='Ending Reason',
                                check_company=True
                                )
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company)
    currency_id = fields.Many2one(string="Currency", related='company_id.currency_id', readonly=True)
    payslip_amount = fields.Monetary()
    last_salary = fields.Monetary(string='Last Salary')
    description = fields.Text(string='Description')
    salary_compensation = fields.Monetary(string='Termination Compensation')
    reward_details = fields.Html(string="Reward Details")
    reward_details_ids = fields.One2many('reward.details', 'eos_id')
    advances_deduction = fields.Float(string='Loans Deduction',
                                      compute="compute_employee_deductions")
    attendance_deduction = fields.Float(string='Attendance Deduction',
                                        compute='compute_employee_deductions')
    gosi_deduction = fields.Float(string='Gosi Deduction',
                                  compute='compute_employee_deductions')
    total_deductions = fields.Float(string='Total Deductions', compute='compute_total_deductions')
    other_deductions = fields.Float(string='Other Deductions', compute='compute_extra_deductions')
    other_additions = fields.Float(string='Other Addition', compute='compute_extra_additions')
    working_days = fields.Integer(string='Working Days', compute='_get_working_days')
    payslip_id = fields.Many2one('hr.payslip', compute="get_payslip")
    department_id = fields.Many2one('hr.department', related='employee_id.department_id', string='Department')
    job_id = fields.Many2one('hr.job', related='employee_id.job_id', string='Job Position')
    unpaid_loans = fields.Float(related='advances_deduction')
    open_bank_loan = fields.Boolean(String='Bank Loans', compute='compute_open_bank_loan')
    slip_count = fields.Integer(compute='get_payslip')
    other_deduction_ids = fields.One2many('eos.extra.deduction', 'eos_id')
    other_dues_ids = fields.One2many('eos.extra.dues', 'eos_id')
    custody = fields.Boolean(String='Custody', compute='compute_not_returned_custody')
    unpaid_leave_month = fields.Float('Unpaid Leave Months')
    unpaid_leave_desc = fields.Char('Unpaid Leave')
    include_compensation = fields.Boolean(related='reason_id.include_compensation', string='Include Compensation')
    compensation_type = fields.Selection([('employee', 'For Employee'), ('company', 'For Company')],
                                         string='Compensation Type')
    # resignation_id = fields.Many2one('hr.employee.resignation')
    last_payslip_date = fields.Date(string='Last Payslip Date', required=True)

    @api.constrains('last_payslip_date', 'last_work_date')
    def _payslip_date_check(self):
        for record in self:
            if record.last_work_date < record.last_payslip_date:
                raise ValidationError(_("Last payslip date should be less than last working date"))

    @api.onchange('compensation_type', 'include_compensation', 'service_years', 'last_work_date')
    def onchange_compensation_type(self):
        if self.include_compensation:
            if self.compensation_type == 'employee':
                self.salary_compensation = self.compute_compensation_amount()
            elif self.compensation_type == 'company':
                self.salary_compensation = -self.compute_compensation_amount()

    def compute_compensation_amount(self):
        compensation_amount = 0.0
        salary = self.contract_id.monthly_yearly_costs
        if self.contract_id.contract_type_id.duration_type == 'limited' or self.contract_id.date_end:
            remaining_period = relativeDelta(self.contract_id.date_end, self.last_work_date)
            days = remaining_period.days + remaining_period.months*30 + (remaining_period.years*12)*30
            months = remaining_period.months + remaining_period.years*12
            compensation_amount = (salary / 30) * days if self.reason_id.min_months_compensation < months else salary*2
        elif self.contract_id.contract_type_id.duration_type == 'unlimited':
            compensation_amount = ((salary / 30) * 15) * self.service_years
        return compensation_amount

    def get_payslip(self):
        for record in self:
            record.payslip_id = self.env['hr.payslip'].search([('eos_id', '=', record.id)], limit=1)
            record.slip_count = len(self.env['hr.payslip'].search([('eos_id', '=', record.id)]))

    @api.depends('employee_id')
    def compute_open_bank_loan(self):
        for record in self:
            bank_loans = self.env['employee.other.loan'].search([('employee_id', '=', record.employee_id.id),
                                                                 ('state', '=', 'confirm')])
            if len(bank_loans) > 0:
                record.open_bank_loan = True
            else:
                record.open_bank_loan

    @api.depends('employee_id')
    def compute_not_returned_custody(self):
        for record in self:
            custody_list = self.env['hr.custody'].search([('employee_id', '=', record.employee_id.id),
                                                                ('state', '=', 'delivered')])
            if len(custody_list) > 0:
                record.custody = True
            else:
                record.custody

    @api.depends('other_deduction_ids', 'other_deduction_ids.amount')
    def compute_extra_deductions(self):
        for record in self:
            record.other_deductions = sum(line.amount for line in record.other_deduction_ids)

    @api.depends('other_dues_ids', 'other_dues_ids.amount')
    def compute_extra_additions(self):
        for record in self:
            record.other_additions = sum(line.amount for line in record.other_dues_ids)

    @api.depends('advances_deduction', 'attendance_deduction',
                 'gosi_deduction', 'other_deductions')
    def compute_total_deductions(self):
        for record in self:
            record.total_deductions = record.advances_deduction + record.attendance_deduction + \
                                      record.gosi_deduction + record.other_deductions

    @api.depends('employee_id', 'last_payslip_date', 'last_work_date')
    def compute_employee_deductions(self):
        for record in self:
            total_ded = 0.0
            loan_ids = self.env['hr.loan.line'].search_read([('employee_id', '=', self.employee_id.id),
                                                             ('paid', '=', False), ('loan_id.state', '=', 'approve')],
                                                            ['amount'])
            record.advances_deduction = sum([line['amount'] for line in loan_ids])
            last_payslip_date = record.last_payslip_date
            if record.last_payslip_date:
                last_day = (record.last_payslip_date.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                if record.last_payslip_date.day == last_day.day:
                    last_payslip_date = last_payslip_date + relativedelta(days=1)
            attendance_ded = self.env['attendance.transaction'].search(
                [('employee_id', '=', record.employee_id.id), ('date', '>=', last_payslip_date),
                 ('date', '<=', record.last_work_date),('status', 'in', ['ex', 'ab']),
                 ('diff_time', '!=', 0)], order='date ASC')
            diff_time = sum(attendance_ded.mapped('diff_time'))
            hours = abs(diff_time) - record.employee_id.allowed_late_hours
            allowance_ids = record.employee_id.contract_id.allowance_ids.filtered(lambda al:
                                                                                al.allowance_type.attendance_deduction)
            wage = record.employee_id.contract_id.wage + sum(allowance_ids.mapped('allowance_amount'))
            if record.employee_id.allowed_late_hours == 0:
                for trans in attendance_ded:
                    shift_calender = trans._get_work_calender(record.employee_id, trans.date)
                    schedule_id = shift_calender.shift_type_id if shift_calender else trans.employee_id.contract_id.resource_calendar_id
                    pl_hours = trans.pl_hours if trans.pl_hours > 0 else 8
                    minute_wage = (wage / 30) / pl_hours / 60 or 0.0
                    if trans.late_in or trans.early_exit:
                        allow_late_in = trans.pl_sign_in_end - trans.pl_sign_in
                        if abs(trans.late_in) > allow_late_in:
                            late_in_deduct = (trans.late_in * 60) * schedule_id.check_in_minute
                            total_ded += (abs(late_in_deduct) * minute_wage)
                        allow_early_exit = trans.pl_sign_out - trans.pl_sign_out_start
                        if abs(trans.early_exit) > allow_early_exit:
                            early_exit_deduct = (trans.early_exit * 60) * schedule_id.check_out_minute
                            total_ded += (abs(early_exit_deduct) * minute_wage)
                    else:
                        total_ded += (abs(trans.diff_time * 60) * minute_wage)

            elif hours > 0:
                deducted_minutes = 0
                for trans in attendance_ded:
                    if trans.late_in or trans.early_exit:
                        allow_late_in = trans.pl_sign_in_end - trans.pl_sign_in
                        if abs(trans.late_in) > allow_late_in:
                            deducted_minutes += abs(trans.late_in)
                        allow_early_exit = trans.pl_sign_out - trans.pl_sign_out_start
                        if abs(trans.early_exit) > allow_early_exit:
                            deducted_minutes += abs(trans.early_exit)
                    else:
                        deducted_minutes += abs(trans.diff_time)
                shift_calender = self.env['attendance.transaction']._get_work_calender(record.employee_id, record.last_payslip_date)
                schedule_id = shift_calender.shift_type_id if shift_calender else record.employee_id.contract_id.resource_calendar_id
                hours_per_day = schedule_id.hours_per_day if schedule_id.hours_per_day > 0 else 8
                minute_wage = (wage / 30) / hours_per_day / 60 or 0.0
                hours = deducted_minutes - record.employee_id.allowed_late_hours
                if hours > 0:
                    deducted_minutes = (hours * 60) * schedule_id.check_out_minute
                    total_ded = abs(deducted_minutes) * minute_wage
            record.attendance_deduction = round(total_ded, 2)

            contract_id = self.contract_id
            gosi_employee_daily = 0.0
            if record.last_work_date:
                last_day_of_month = monthrange(self.last_work_date.year, self.last_work_date.month)[1]
                if record.last_work_date.day == last_day_of_month or record.last_work_date.day == 1:
                    gosi_employee_daily = contract_id.gosi_employee_daily
                else:
                    gosi_id = self.env['gosi.daily.contribution'].search([('sequence', '=', self.last_work_date.month),
                                                                          ('contract_id', '=', contract_id.id)], limit=1)
                    gosi_employee_daily = gosi_id.gosi_employee_daily
            record.gosi_deduction = gosi_employee_daily * self.working_days
            gross_salary = (self.employee_id.contract_id.monthly_yearly_costs / 30) * self.working_days
            self.payslip_amount = gross_salary

    def action_unpaid_cash_loans(self):
        return {
            'name': _('Unpaid Loans'),
            'view_mode': 'tree',
            'res_model': 'hr.loan',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('plustech_hr_loan.hr_unpaid_loan_tree_view').id,
            'context': {'create': 0, 'delete': 0, 'edit': 0, 'duplicate': 0},
            'domain': [('state', '=', 'approve'), ('balalncen_amount', '>', 0.0)]
        }

    def action_bank_loans(self):
        return {
            'name': _('Bank Loans'),
            'view_mode': 'tree',
            'res_model': 'employee.other.loan',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('plustech_hr_loan.employee_other_loan_tree_view').id,
            'context': {'create': 0, 'delete': 0, 'edit': 0, 'duplicate': 0},
            'domain': [('employee_id', '=', self.employee_id.id), ('state', '=', 'confirm')]
        }

    def action_open_custody(self):
        return {
            'name': _('Custody'),
            'view_mode': 'tree',
            'res_model': 'hr.custody',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('plustech_hr_custody.employee_custody_view_tree').id,
            'context': {'create': 0, 'delete': 0, 'edit': 0, 'duplicate': 0},
            'domain': [('employee_id', '=', self.employee_id.id), ('state', '=', 'delivered')]
        }

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            seq_date = None
            if 'request_date' in vals:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['request_date']))
            vals['name'] = self.env['ir.sequence'].next_by_code('end.of.service', sequence_date=seq_date) or _('New')
        result = super(EndOfServiceReward, self).create(vals)
        return result

    @api.depends('last_work_date', 'employee_id', 'last_payslip_date')
    def _get_working_days(self):
        fmt = '%Y-%m-%d'
        payslip = self.env['hr.payslip'].search([('employee_id', '=', self.employee_id.id), ('state', '=', 'paid')])
        if payslip and self.last_work_date:
            to_date = payslip.mapped('date_to')
            latest = max(to_date)
            d1 = datetime.strptime(str(latest), fmt)
            d2 = datetime.strptime(str(self.last_work_date), fmt)
            self.working_days = (d2 - d1).days
            last_payslip = self.env['hr.payslip'].search([('date_to', '=', latest.strftime('%Y-%m-%d'))], limit=1)
            self.last_salary = last_payslip.gross_wage
        days = 0
        if self.last_payslip_date and self.last_work_date:
            d1 = datetime.strptime(str(self.last_payslip_date), fmt)
            d2 = datetime.strptime(str(self.last_work_date), fmt)
            days = (d2 - d1).days
            if self.last_work_date.month == 2 and self.last_work_date.day == 28:
                days = (d2 - d1).days + 2
            if self.last_work_date.month == 2 and self.last_work_date.day == 29:
                days = (d2 - d1).days + 1
            if d1.day == d2.day:
                if d1.month == 2:
                    days = (d2 - d1).days + 1 if is_leap_year(d1.year) else (d2 - d1).days + 2
                else:
                    days = (d2 - d1).days - 1
        self.working_days = days

    def action_view_payslip(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.payslip',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.payslip_id.id,
            'views': [(False, 'form')],
        }

    @api.depends('employee_id', 'last_work_date')
    def _compute_remaining_leave_balance(self):
        for record in self:
            if record.employee_id:
                allocations = self.env['hr.leave.allocation'].search([('holiday_status_id.is_annual_leave', '=', True),
                                                                      ('employee_id', '=', record.employee_id.id),
                                                                      ('state', '=', 'validate')])
                balance = sum([rec.number_of_days - rec.leaves_taken for rec in allocations])
                days = 0
                sign = 1
                accrual_allocations = allocations.filtered(lambda al: al.allocation_type == 'accrual')
                if accrual_allocations and record.last_work_date:
                    current_level = allocations[0]._get_current_accrual_plan_level_id(record.last_work_date)
                    nextcall = allocations[0].date_from
                    if allocations[0].nextcall:
                        nextcall = allocations[0].nextcall
                    date_from = nextcall - timedelta(days=1)
                    date_to = record.last_work_date
                    delta = date_to - date_from
                    if date_from > date_to:
                        date_from = record.last_work_date
                        sign = -1
                    z = 0
                    for i in range(abs(delta.days)):
                        end_date = date_from + timedelta(days=i)
                        days += allocations[0]._process_accrual_plan_level(current_level[0], date_from, date_from,
                                                                           end_date, end_date)
                        z += 1
                        days = days
                record.remaining_leaves = balance + (days * sign)
            else:
                record.remaining_leaves = 0.0
            contract_id = record.contract_id
            allowance_ids = contract_id.allowance_ids.filtered(lambda line: line.leave_compensation)
            allowances = [contract_id.get_allowance(line.allowance_type.code) for line in allowance_ids]
            month_days = record.company_id.days_per_year/12
            leave_compensation = (contract_id.wage + sum(allowances)) / month_days
            record.leave_balance_reward = round(leave_compensation * record.remaining_leaves)

    @api.depends('join_date', 'last_work_date', 'employee_id')
    def _calc_service_year(self):
        for record in self:
            unpaid_leave_delta = relativedelta()
            unpaid_leave_ids = self.env['hr.leave'].sudo().search([('employee_id', '=', record.employee_id.id),
                                                                   ('state', '=', 'validate'),
                                                                   ('holiday_status_id.unpaid', '=', True)])
            unpaid_leave_days = 0
            for leave_id in unpaid_leave_ids:
                unpaid_leave_delta += relativeDelta(leave_id.date_to, leave_id.date_from)
                unpaid_leave_days += (leave_id.date_to - leave_id.date_from).days
            record.unpaid_leave_desc = delta_desc(unpaid_leave_delta)
            record.unpaid_leave_month = (unpaid_leave_delta.years * 12) + (unpaid_leave_delta.months) + (
                    unpaid_leave_delta.days / 30.0)
            last_date = self.last_work_date - timedelta(days=unpaid_leave_days) \
                if unpaid_leave_days > 0 else record.last_work_date
         
            if self.env.company.month_type == '0':
                record.service_years = 0
                record.service_months = 0
                record.service_days = 0
                service_month = 0
                if last_date and record.join_date:
                    delta = last_date - record.join_date
                    if int(self.env.company.days_of_month) == 0:
                        raise ValidationError(_('Month Days Must Bigger than Zero'))
                    record.service_years = delta.days / int(self.env.company.days_of_month) / 12
                    record.service_months = delta.days / int(self.env.company.days_of_month)
                    record.service_days = delta.days
                    service_month = delta.days / int(self.env.company.days_of_month)
            else:
                delta = relativedelta(last_date, record.join_date)
                record.service_years = delta.years
                record.service_months = delta.months
                record.service_days = delta.days
                service_month = (delta.years * 12) + (delta.months) + (delta.days / 30.0)
            service_year = service_month / 12.0
            record.total_service_year = service_year
            if record.last_work_date and record.employee_id and record.reason_id:
                net_period_reward_amount = record.get_eos_amount(service_year)
                record.deserving = round(net_period_reward_amount)

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        for record in self:
            payslip = self.env['hr.payslip'].search([('employee_id', '=', self.employee_id.id), ('state', '=', 'paid')])
            if payslip:
                to_date = payslip.mapped('date_to')
                latest = max(to_date)
                record.last_payslip_date = latest

    def get_eos_amount(self, service_years):
        reward_amount = 0.0
        actual_years = service_years
        contract_id = self.contract_id
        if self.reason_id.includ_allowance:
            gross_salary = sum(
                [contract_id.get_allowance(line.allowance_type.code) for line in contract_id.allowance_ids])
        else:
            gross_salary = sum([contract_id.get_allowance(line.code) for line in self.reason_id.allowance_ids])
        gross_salary = gross_salary + contract_id.wage
        ranges =  self.reason_id.rule_id.sorted(key=lambda line: line.period_from, reverse=False)
        if service_years >= ranges[0].period_from:
            for eos_rule in ranges:
                diff = service_years - eos_rule.period_to
                tmp_entitlements = gross_salary * eos_rule.eos_award * (service_years if diff <= 0 else eos_rule.period_to)
                reward_amount += tmp_entitlements
                service_years = service_years - eos_rule.period_to
                if service_years <= 0:
                    break
        reward_amount = round(reward_amount, 2)
        self.net_period_reward = reward_amount
        calculate_factors = self.reason_id.rule_id.filtered(lambda line: line.period_from <= actual_years).mapped('calculate_factor')
        if len(calculate_factors) == 0 or not contract_id.contract_type_id.end_of_service:
            return 0
        return reward_amount * calculate_factors[len(calculate_factors) - 1]

    @api.depends('join_date', 'last_work_date')
    def _compute_number_of_days_from_join_date(self):
        for record in self:
            record.number_of_days_from_join_date = 0
            if record.last_work_date and record.join_date:
                number_of_days_from_join_date = record.last_work_date - record.join_date
                record.number_of_days_from_join_date = number_of_days_from_join_date.days

    @api.depends('deserving', 'leave_balance_reward', 'salary_compensation', 'other_additions', 'payslip_amount')
    def _compute_total_reward(self):
        for record in self:
            record.total_reward = record.deserving + record.leave_balance_reward \
                                  + record.salary_compensation + record.other_additions + record.payslip_amount

    @api.depends('total_reward', 'salary_compensation', 'payslip_amount', 'total_deductions')
    def _compute_final_deserving(self):
        self.final_deserving = self.total_reward - self.total_deductions

    def action_submit(self):
        self.write({'state': 'submit'})

    def action_hro_approve(self):
        self.state = 'hro'

    def action_hrm_approval(self):
        self.state = "hrm"

    def action_reset_to_draft(self):
        self.state = 'draft'

    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise ValidationError(_('You Can Not Delete a Request Which Is Not Draft.'))
            res = super(EndOfServiceReward, record).unlink()
            return res

    def action_generate_payslip(self):
        payslips = self.env['hr.payslip']
        for rec in self:
            from_date = rec.last_payslip_date + relativedelta(days=1)
            to_date = rec.last_work_date
            employee = rec.employee_id
            contract_id = rec.employee_id.contract_id
            action = self.env["ir.actions.actions"]._for_xml_id(
                'hr_payroll.action_view_hr_payslip_month_form')
            action.update({'view_mode': 'form',
                           'views': [(False, 'form')],
                           'context': {
                               'default_employee_id': employee.id,
                               'default_contract_id': contract_id.id,
                               'default_date_from': from_date,
                               'default_date_to': to_date,
                               'default_eos_id': self.id,
                               'default_name': _('EOS for %s' % employee.name),

                           }
                           })
            return action

    def get_loan(self, payslip):
        loan_ids = self.env['hr.loan.line'].search([('employee_id', '=', self.employee_id.id)])
        loan_ids = loan_ids.filtered(lambda line: line.loan_id.state == 'approve')
        payslip.loan_ids = loan_ids
        for lo in payslip.loan_ids:
            lo.paid = True

    def action_generate_payment(self):
        result = self.env.ref('account.action_account_payments').read()[0]
        view_id = self.env.ref('account.view_account_payment_form').id
        result.update({'views': [(view_id, 'form')], })
        result['context'] = {
            'default_partner_id': self.employee_id.address_home_id.id,
            'default_payment_type': 'outbound',
            'default_amount': self.final_deserving,
            'default_journal_id': self.reason_id.journal_id.id,
            'default_eos_id': self.id
        }
        return result


class RewardDetails(models.Model):
    _name = "reward.details"
    _description = 'EOS Reward details'

    period = fields.Char(string='Period')
    reward = fields.Float(string='Reward')
    eos_id = fields.Many2one('end.of.service.reward')


class ExtraDeductions(models.Model):
    _name = 'eos.extra.deduction'
    _description = 'End Of Service Other Deductions'
    _rec_name = 'input_id'

    input_id = fields.Many2one('eos.other.input', string='Description',
                               domain=[('input_type', '=', 'deduction')])
    amount = fields.Float(string='Amount')
    note = fields.Text(string='Notes')
    eos_id = fields.Many2one('end.of.service.reward')


class ExtraDeductions(models.Model):
    _name = 'eos.extra.dues'
    _description = 'End Of Service Other Dues'
    _rec_name = 'input_id'

    input_id = fields.Many2one('eos.other.input', string='Description',
                               domain=[('input_type', '=', 'allowance')])
    amount = fields.Float(string='Amount')
    note = fields.Text(string='Notes')
    eos_id = fields.Many2one('end.of.service.reward')


class EosOtherInput(models.Model):
    _name = 'eos.other.input'
    _description = 'EOS Other Input'

    name = fields.Char(string='Description', translate=True, required=True)
    input_type = fields.Selection([('allowance', 'Allowance'), ('deduction', 'Deduction')],
                                  string='Input Type', required=True)
