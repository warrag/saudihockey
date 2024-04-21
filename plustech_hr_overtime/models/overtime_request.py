# -*- coding: utf-8 -*-

from dateutil import relativedelta
from datetime import timedelta
import pandas as pd
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.resource.models.resource import HOURS_PER_DAY

STATUS = [('draft', 'Draft'),
          ('dm_approve', 'Waiting For Manager Approval'),
          ('hr_approve', 'Waiting For HR Approval'),
          ('hrm', 'Waiting HRM Approval'), ('finance', 'Waiting Finance Approval'),
          ('ceo', 'Waiting CEO Approval'), ('to_pay', 'To Pay'), ('paid', 'Paid'),
          ('done', 'Done'), ('refused', 'Refused'), ('cancel', 'Cancelled')
          ]


class HrOverTime(models.Model):
    _name = 'hr.overtime'
    _description = "HR Overtime"
    _inherit = ['mail.thread']

    def _get_employee_domain(self):
        employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.user.id)], limit=1)
        domain = [('id', '=', employee.id)]
        if self.env.user.has_group('hr.group_hr_user'):
            domain = []
        return domain

    def _default_employee(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    @api.model
    def _default_journal_id(self):
        """ The journal is determining the company of the accounting entries generated from overtime request. We need to
        force journal company and business trip  company to be the same. """
        default_company_id = self.default_get(['company_id'])['company_id']
        journal = self.env['account.journal'].search(
            [('type', '=', 'purchase'), ('company_id', '=', default_company_id)], limit=1)
        return journal.id

    @api.onchange('days_no_tmp')
    def _onchange_days_no_tmp(self):
        self.days_no = self.days_no_tmp

    def _get_default_overtime_product_id(self):
        default_company_id = self.env.company
        return default_company_id.overtime_product_id

    name = fields.Char('Name', readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  domain=_get_employee_domain, default=lambda self: self.env.user.employee_id.id,
                                  required=True)
    employee_number = fields.Char(related='employee_id.employee_number', string='Employee Number')
    department_id = fields.Many2one('hr.department', string="Department",
                                    related="employee_id.department_id", store=True)
    job_id = fields.Many2one('hr.job', string="Job Position", related="employee_id.job_id")
    manager_id = fields.Many2one('res.users', string="Manager",
                                 related="employee_id.parent_id.user_id", store=True)
    contract_id = fields.Many2one('hr.contract', string="Contract",
                                  related="employee_id.contract_id",
                                  )
    request_date = fields.Date('Request Date', default=fields.Date.today())
    date_from = fields.Date('Date From')
    date_to = fields.Date('Date to')
    days_no_tmp = fields.Float('Hours', compute="_get_days", store=True, readonly=False)
    days_no = fields.Float('No. of Days', store=True)
    desc = fields.Text('Description')
    state = fields.Selection(STATUS, string="state",
                             default="draft")
    cancel_reason = fields.Text('Refuse Reason')
    leave_id = fields.Many2one('hr.leave.allocation',
                               string="Leave ID")
    attchd_copy = fields.Binary('Attach A File')
    attchd_copy_name = fields.Char('File Name')
    type = fields.Selection([('cash', 'Cash'), ('leave', 'leave')], default="leave", required=True, string="Type")
    overtime_type_id = fields.Many2one('overtime.type', domain="[('type','=',type),('duration_type','=', "
                                                               "duration_type)]")
    public_holiday = fields.Char(string='Public Holiday', readonly=True)
    attendance_ids = fields.Many2many('hr.attendance', string='Attendance')
    work_schedule = fields.One2many(
        related='employee_id.resource_calendar_id.attendance_ids')
    global_leaves = fields.One2many(
        related='employee_id.resource_calendar_id.global_leave_ids')
    duration_type = fields.Selection([('hours', 'Hour'), ('days', 'Days')], string="Duration Type", default="hours",
                                     required=True)
    cash_hrs_amount = fields.Float(string='Overtime Amount', readonly=True)
    cash_day_amount = fields.Float(string='Overtime Amount', readonly=True)
    payslip_paid = fields.Boolean('Paid in Payslip', readonly=True)
    hours_per_day = fields.Float(string='Dialy Hours')
    schedule_ids = fields.One2many('overtime.schedule', 'overtime_id')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)
    accounting_date = fields.Date("Accounting Date")
    journal_id = fields.Many2one('account.journal', string='Expense Journal',
                                 states={'done': [('readonly', True)], 'post': [('readonly', True)]},
                                 check_company=True,
                                 domain="[('type', '=', 'purchase'), ('company_id', '=', company_id)]",
                                 default=_default_journal_id, help="The journal used when the overtime is done.")
    account_move_id = fields.Many2one('account.move', string='Journal Entry', ondelete='restrict', copy=False,
                                      readonly=True)
    overtime_product_id = fields.Many2one('product.product', string='Overtime Product',
                                          default=_get_default_overtime_product_id)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account',
                                          default=lambda
                                              self: self.env.company.overtime_analytic_account_id)
    overtime_payment = fields.Selection([('payroll', 'Payroll'), ('finance', 'Finance')],
                                        string='Payment Options', default=lambda self: self.env.company.overtime_payment)
    currency_id = fields.Many2one(related='company_id.currency_id', readonly=True)
    is_employee = fields.Boolean(compute='request_owner')
    current_user_id = fields.Many2one('res.users', compute='get_current_user')
    is_manager = fields.Boolean(compute='get_current_uid')
    amount_residual = fields.Monetary(string='Amount Due', compute='_compute_amount_residual')
    duration = fields.Float('Duration', store=True, compute="_compute_duration")
    total_hours = fields.Float('Total Hours', compute="_get_total_hours", store=True)

    @api.depends('date_from', 'date_to')
    def _compute_duration(self):
        for recd in self:
            if recd.date_from and recd.date_to:
                if recd.date_from > recd.date_to:
                    raise ValidationError('Start Date must be less than End Date')
        for sheet in self:
            days_no = 0
            if sheet.date_from and sheet.date_to:
                start_dt = sheet.date_from
                finish_dt = sheet.date_to + timedelta(days=1)
                days_no = (finish_dt - start_dt).days
            sheet.duration = days_no

    @api.depends("account_move_id.line_ids")
    def _compute_amount_residual(self):
        for record in self:
            if not record.currency_id or record.currency_id == record.company_id.currency_id:
                residual_field = 'amount_residual'
            else:
                residual_field = 'amount_residual_currency'
            payment_term_lines = record.account_move_id.sudo().line_ids \
                .filtered(
                lambda line: line.overtime_id == record and line.account_internal_type in ('receivable', 'payable'))
            record.amount_residual = -sum(payment_term_lines.mapped(residual_field))

    @api.depends('manager_id')
    def get_current_uid(self):
        """

        :param self:
        :return:
        """
        if self.manager_id.user_id.id == self.env.user.id:
            self.is_manager = True
        else:
            self.is_manager = False

    @api.depends('current_user_id')
    def request_owner(self):
        for record in self:
            if record.current_user_id == record.employee_id.user_id:
                record.is_employee = True
            else:
                record.is_employee = False

    def get_current_user(self):
        for record in self:
            record.current_user_id = self.env.user

    def generate_schedule(self):
        self.schedule_ids = None
        schedule_obj = self.env['overtime.schedule']
        delta = self.date_to - self.date_from
        days = self.get_period_days(self.date_from, delta)
        lines = []
        hours = self.days_no_tmp if self.duration_type == 'hours' else self.hours_per_day
        for day in days:
            vals = {
                'date': day,
                'overtime_id': self.id,
                'week_day': f'{day.weekday()}',
                'working_hours': hours
            }
            lines.append(vals)
        schedule_obj.create(lines)

    @api.depends('schedule_ids', 'schedule_ids.working_hours')
    def _get_total_hours(self):
        for record in self:
            record.total_hours = sum(record.schedule_ids.mapped('working_hours'))

    def get_period_days(self, date_from, delta):
        all_period_date = []
        for i in range(delta.days + 1):
            day = date_from + timedelta(days=i)
            all_period_date.append(day)
        return all_period_date

    @api.onchange('employee_id')
    def _get_defaults(self):
        for sheet in self:
            if sheet.employee_id:
                sheet.update({
                    'department_id': sheet.employee_id.department_id.id,
                    'job_id': sheet.employee_id.job_id.id,
                    'manager_id': sheet.sudo().employee_id.parent_id.user_id.id,
                })

    @api.depends('date_from', 'date_to', 'duration_type')
    def _get_days(self):
        for recd in self:
            if recd.date_from and recd.date_to:
                if recd.date_from > recd.date_to:
                    raise ValidationError('Start Date must be less than End Date')
        for sheet in self:
            if sheet.date_from and sheet.date_to:
                start_dt = fields.Datetime.from_string(sheet.date_from)
                finish_dt = fields.Datetime.from_string(sheet.date_to)
                s = finish_dt - start_dt
                difference = relativedelta.relativedelta(finish_dt, start_dt)
                hours = difference.hours
                minutes = difference.minutes
                days_in_mins = s.days * 24 * 60
                hours_in_mins = hours * 60
                days_no = ((days_in_mins + hours_in_mins + minutes) / (24 * 60))

                diff = sheet.date_to - sheet.date_from
                days, seconds = diff.days, diff.seconds
                hours = days * 24 + seconds // 3600
                sheet.update({
                    'days_no_tmp': hours if sheet.duration_type == 'hours' else days_no + 1,
                })

    @api.onchange('overtime_type_id')
    def _get_hour_amount(self):
        for rec in self:
            if rec.duration_type == 'hours' and rec.overtime_type_id:
                cash_amount = 0.0
                if rec.contract_id and not rec.contract_id.over_hour:
                    raise UserError(_("Hour Overtime Needs Hour Wage in Employee Contract."))
                if rec.overtime_type_id.rule_line_ids:
                    for record in rec.overtime_type_id.rule_line_ids:
                        if record.from_hrs < self.days_no_tmp <= record.to_hrs and self.contract_id:
                            cash_amount = self.total_hours * record.hrs_amount
                else:
                    cash_amount = self.contract_id.over_hour * self.duration
                self.cash_hrs_amount = cash_amount

            elif rec.duration_type == 'days':
                if not self.contract_id.over_day:
                    raise UserError(_("Day Overtime Needs Day Wage in Employee Contract."))
                if rec.overtime_type_id.rule_line_ids:
                    for recd in self.overtime_type_id.rule_line_ids:
                        if recd.from_hrs < self.days_no_tmp <= recd.to_hrs and self.contract_id:
                            if self.contract_id.over_day:
                                cash_amount = self.total_hours * recd.hrs_amount
                else:
                    cash_amount = self.contract_id.over_day * self.total_hours
                self.cash_day_amount = cash_amount

    def action_submit(self):
        if self.env.user == self.employee_id.user_id or self.env.user != self.manager_id.user_id:
            self.write({'state': 'dm_approve'})
        else:
            self.write({'state': 'hr_approve'})

    def action_direct_manager_approve(self):
        self.write({'state': 'hr_approve'})

    def action_hr_office_approve(self):
        self.write({'state': 'hrm'})

    def action_hrm_approve(self):
        self.write({'state': 'ceo'})

    def action_ceo_approve(self):
        if self.overtime_type_id.type == 'leave':
            self.approve_leave_balance()
        else:
            self.write({'state': 'to_pay'})

    def approve_leave_balance(self):
        if self.overtime_type_id.type == 'leave':
            if self.duration_type == 'days':
                holiday_vals = {
                    'name': 'Overtime',
                    'holiday_status_id': self.overtime_type_id.leave_type.id,
                    'number_of_days': self.days_no_tmp,
                    'notes': self.desc,
                    'holiday_type': 'employee',
                    'employee_id': self.employee_id.id,
                    'state': 'validate',
                }
            else:
                day_hour = self.days_no_tmp / HOURS_PER_DAY
                holiday_vals = {
                    'name': 'Overtime',
                    'holiday_status_id': self.overtime_type_id.leave_type.id,
                    'number_of_days': day_hour,
                    'notes': self.desc,
                    'holiday_type': 'employee',
                    'employee_id': self.employee_id.id,
                    'state': 'validate',
                }
            holiday = self.env['hr.leave.allocation'].create(
                holiday_vals)
            self.leave_id = holiday.id
        return self.sudo().write({
            'state': 'done',

        })

    def action_refuse(self):
        self.state = 'refused'

    @api.constrains('date_from', 'date_to')
    def _check_date(self):
        for req in self:
            domain = [
                ('date_from', '<=', req.date_to),
                ('date_to', '>=', req.date_from),
                ('employee_id', '=', req.employee_id.id),
                ('id', '!=', req.id),
                ('state', 'not in', ['refused']),
            ]
            no_holidays = self.search_count(domain)
            if no_holidays:
                raise ValidationError(_(
                    'You can not have 2 Overtime requests that overlaps on same day!'))

    @api.model
    def create(self, values):
        seq = self.env['ir.sequence'].next_by_code('hr.overtime') or '/'
        values['name'] = seq
        return super(HrOverTime, self.sudo()).create(values)

    def unlink(self):
        for rec in self.filtered(
                lambda overtime: overtime.state != 'draft'):
            raise UserError(
                _('You cannot delete overtime request which is not in draft state.'))
        return super(HrOverTime, self).unlink()

    @api.onchange('date_from', 'date_to', 'employee_id')
    def _onchange_date(self):
        holiday = False
        if self.contract_id and self.date_from and self.date_to:
            for leaves in self.contract_id.sudo().resource_calendar_id.global_leave_ids:
                leave_dates = pd.date_range(leaves.date_from, leaves.date_to).date
                overtime_dates = pd.date_range(self.date_from, self.date_to).date
                for over_time in overtime_dates:
                    for leave_date in leave_dates:
                        if leave_date == over_time:
                            holiday = True
            if holiday:
                self.sudo().write({
                    'public_holiday': 'You have Public Holidays in your Overtime request.'})
            else:
                self.sudo().write({'public_holiday': ' '})
            hr_attendance = self.env['hr.attendance'].sudo().search(
                [('check_in', '>=', self.date_from),
                 ('check_in', '<=', self.date_to),
                 ('employee_id', '=', self.employee_id.id)])
            self.sudo().update({
                'attendance_ids': [(6, 0, hr_attendance.ids)]
            })

    def _get_expense_account_source(self, product_id):
        self.ensure_one()

        if product_id:
            account = product_id.product_tmpl_id.with_company(self.company_id)._get_product_accounts()['expense']
            if not account:
                raise UserError(
                    _("No Expense account found for the product %s (or for its category), please configure one.") % (
                        self.product_id.name))
        else:
            account = self.env['ir.property'].with_company(self.company_id)._get('property_account_expense_categ_id',
                                                                                 'product.category')
            if not account:
                raise UserError(
                    _('Please configure Default Expense account for Category expense: `property_account_expense_categ_id`.'))
        return account

    def _get_expense_account_destination(self):
        self.ensure_one()
        if not self.employee_id.sudo().address_home_id:
            raise UserError(
                _("No Home Address found for the employee %s, please configure one.") % (self.employee_id.name))
        partner = self.employee_id.sudo().address_home_id.with_company(self.company_id)
        account_dest = partner.property_account_payable_id or partner.parent_id.property_account_payable_id
        return account_dest.id

    def _prepare_move_values(self):
        """
        This function prepares move values related to an expense
        """
        self.ensure_one()
        journal = self.journal_id
        account_date = self.accounting_date or self.date_to
        move_values = {
            'journal_id': journal.id,
            'company_id': self.company_id.id,
            'date': account_date,
            'ref': self.name,
            # force the name to the default value, to avoid an eventual 'default_name' in the context
            # to set it to '' which cause no number to be given to the account.move when posted.
            'name': '/',
        }
        return move_values

    def _get_account_move_line_values(self):
        move_line_values = {}
        for record in self:
            move_line_name = record.employee_id.name + ': ' + record.name.split('\n')[0][:64]
            account_date = self.accounting_date or record.date_to or fields.Date.context_today(record)
            overtime_product_id = record.overtime_product_id or self.company_id.overtime_product_id
            account_src = record._get_expense_account_source(overtime_product_id)
            account_dst = record._get_expense_account_destination()
            move_line_values = []
            unit_amount = record.cash_day_amount if record.duration_type == 'days' else record.cash_hrs_amount
            partner_id = record.employee_id.sudo().address_home_id.commercial_partner_id.id
            # source move line
            move_line_src = {
                'name': move_line_name,
                'quantity': 1,
                'debit': unit_amount if unit_amount > 0 else 0,
                'credit': unit_amount < 0 and -unit_amount or 0,
                'account_id': account_src.id,
                'product_id': overtime_product_id.id,
                'product_uom_id': overtime_product_id.uom_id.id,
                'analytic_account_id': record.analytic_account_id.id,
                'overtime_id': record.id,
                'partner_id': partner_id,
                'currency_id': record.currency_id.id,
            }
            move_line_values.append((0, 0, move_line_src))
            move_line_dst = {
                'name': move_line_name,
                'debit': unit_amount < 0 and -unit_amount or 0,
                'credit': unit_amount > 0 and unit_amount or 0,
                'account_id': account_dst,
                'date_maturity': account_date,
                'currency_id': record.currency_id.id,
                'partner_id': partner_id,
                'overtime_id': record.id,
                'exclude_from_invoice_tab': True,
            }
            move_line_values.append((0, 0, move_line_dst))
        return move_line_values

    def action_move_create(self):
        for record in self:
            move_vals = record._prepare_move_values()
            move_vals['line_ids'] = self._get_account_move_line_values()
            move = self.env['account.move'].with_context(default_journal_id=move_vals['journal_id']).create(move_vals)
            if move:
                record.account_move_id = move.id

    def action_register_payment(self):
        return {
            'name': _('Register Payment'),
            'res_model': 'account.payment.register',
            'view_mode': 'form',
            'context': {
                'active_model': 'account.move',
                'active_ids': self.account_move_id.ids,
                'default_partner_bank_id': self.employee_id.sudo().bank_account_id.id,
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def action_open_account_move(self):
        self.ensure_one()
        return {
            'name': self.account_move_id.name,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.account_move_id.id
        }


class OvertimeSchedule(models.Model):
    _name = 'overtime.schedule'
    _description = 'Overtime Schedule'

    overtime_id = fields.Many2one('hr.overtime', required=True, ondelete='cascade', index=True, copy=False)
    date = fields.Date(string='Date')
    week_day = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ], 'Day of Week', required=True, index=True, )
    working_hours = fields.Float(string='Working Hours')
