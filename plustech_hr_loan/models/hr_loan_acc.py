# -*- coding: utf-8 -*-
import time
from odoo import models, fields, api, _
from odoo.exceptions import except_orm, ValidationError
import time
from datetime import datetime, date, time, timedelta
import dateutil.parser
import pytz
from pytz import timezone, UTC


class HrLoanAcc(models.Model):
    _inherit = 'hr.loan'

    def action_approve(self):
        """
        This create account move for request.
        """
        contract_obj = self.env['hr.contract'].sudo().search([('employee_id', '=', self.employee_id.id)])
        if not contract_obj:
            raise ValidationError(_('You must Define a contract for employee'))
        if not self.loan_lines:
            raise ValidationError(_('You must compute installment before Approved'))
        self.write({'state': 'acceptance'})

    def action_double_approve(self):
        """This create account move for request in case of double approval.
            """
        if not self.loan_account_id or not self.treasury_account_id or not self.loan_journal_id:
            raise ValidationError(_("You must enter employee account & Treasury account and journal to approve "))
        if not self.loan_lines:
            raise ValidationError(_('You must compute Loan Request before Approved'))
        timenow = fields.Datetime.today()
        for loan in self:
            amount = loan.loan_amount
            loan_name = loan.employee_id.name
            reference = loan.name
            journal_id = loan.loan_journal_id.id
            debit_account_id = loan.loan_account_id.id
            credit_account_id = loan.treasury_account_id.id
            analytic_account_id = loan.analytic_account_id

            debit_vals = {
                'name': loan_name,
                'account_id': debit_account_id,
                'journal_id': journal_id,
                'date': timenow,
                'debit': amount > 0.0 and amount or 0.0,
                'credit': amount < 0.0 and -amount or 0.0,
                'loan_id': loan.id,
                'analytic_account_id': analytic_account_id.id,
            }
            credit_vals = {
                'name': loan_name,
                'account_id': credit_account_id,
                'journal_id': journal_id,
                'date': timenow,
                'debit': amount < 0.0 and -amount or 0.0,
                'credit': amount > 0.0 and amount or 0.0,
                'loan_id': loan.id,
                'analytic_account_id': analytic_account_id.id,
            }
            vals = {
                'ref': 'Loan For' + ' ' + loan_name,
                'narration': loan_name,
                # 'ref': reference,
                'journal_id': journal_id,
                'date': timenow,
                'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
            }
            move = self.env['account.move'].create(vals)
            move.post()
        self.write({'state': 'approve'})
        self.loan_lines.write({'state': 'pending'})
        return True


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    loan_id = fields.Many2one('hr.loan', string="Loan")


class HrLoanLineAcc(models.Model):
    _inherit = "hr.loan.line"

    def action_paid_amount(self):
        """This create the account move line for payment of each installment.
            """
        timenow = fields.Datetime.today()
        for line in self:
            if line.loan_id.state != 'approve':
                raise ValidationError(_("Loan Request must be approved"))
            amount = line.amount
            loan_name = line.employee_id.name
            reference = line.loan_id.name
            journal_id = line.loan_id.loan_journal_id.id
            credit_account_id = line.loan_id.loan_account_id.id
            debit_account_id = line.loan_id.treasury_account_id.id
            analytic_account_id = line.loan_id.analytic_account_id

            employee_id = self.env['hr.employee'].browse(self.employee_id.id)
            debit_vals = {
                'name': loan_name,
                'account_id': debit_account_id,
                'journal_id': journal_id,
                'date': timenow,
                'debit': amount > 0.0 and amount or 0.0,
                'credit': amount < 0.0 and -amount or 0.0,
                'loan_id': line.loan_id.id,
                'analytic_account_id': analytic_account_id.id or employee_id.contract_id.analytic_account_id.id or False,
            }
            credit_vals = {
                'name': loan_name,
                'account_id': credit_account_id,
                'journal_id': journal_id,
                'date': timenow,
                'debit': amount < 0.0 and -amount or 0.0,
                'credit': amount > 0.0 and amount or 0.0,
                'loan_id': line.loan_id.id,
                'analytic_account_id': analytic_account_id.id or employee_id.contract_id.analytic_account_id.id or False,
            }
            vals = {
                'ref': 'Loan Deduction For ' + ' ' + loan_name,
                'narration': loan_name,
                # 'ref': reference,
                'journal_id': journal_id,
                'date': timenow,
                'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
            }
            move = self.env['account.move'].create(vals)
            move.action_post()
        return True


class HrPayslipAcc(models.Model):
    _inherit = 'hr.payslip'

    def compute_sheet(self):
        res = super(HrPayslipAcc, self).compute_sheet()
        if len(self.loan_ids) == 0:
            for rec in self:
                rec.get_loan()

                for lo in rec.loan_ids:
                    lo.paid = True
                loan_count = self.env['hr.loan.line'].search([('employee_id', 'in', rec.employee_id.ids),
                                                              ('date', '>=', rec.date_from),
                                                              ('date', '<=', rec.date_to),
                                                              ('paid', '=', False)])

            if loan_count:
                raise ValidationError(_('Please Update the Loans'))
            else:

                res = super(HrPayslipAcc, self).compute_sheet()
                return res
        else:
            return res

    @api.model
    def get_abs(self, obj, amount_per_day=0):
        HrAbsent = self.env['hr.absent']
        HrEmployee = self.env['hr.employee'].sudo()
        HrAttendance = self.env['hr.attendance'].sudo()
        ResourceCalendarLeaves = self.env['resource.calendar.leaves'].sudo()
        HrLeave = self.env['hr.leave'].sudo()
        absent_ids = HrAbsent.search([])
        absent_ids.unlink()
        day_count = ((obj.date_to + timedelta(days=1)) - obj.date_from).days
        employee_id = HrEmployee.browse(obj.employee_id)
        count = 0
        if employee_id.contract_id.state == 'open':
            tz = employee_id.tz
            global_leave_ids = employee_id.resource_calendar_id.global_leave_ids
            for single_date in (obj.date_from + timedelta(n) for n in range(day_count)):
                absent_id = HrAbsent
                if global_leave_ids:
                    global_leave = ResourceCalendarLeaves.search([
                        ('id', 'in', global_leave_ids.ids),
                        ('date_from_date', '<=', single_date),
                        ('date_to_date', '>=', single_date)
                    ])
                    if global_leave:
                        absent_id = HrAbsent.create({
                            'employee_id': employee_id.id,
                            'date': single_date,
                            'type': 'global_time_off'
                        })
                if not absent_id:
                    leave_id = HrLeave.search([
                        ('employee_id', '=', employee_id.id),
                        ('request_date_from', '<=', single_date),
                        ('request_date_to', '>=', single_date),
                        ('state', '=', 'validate'),
                    ])
                    if leave_id:
                        absent_id = HrAbsent.create({
                            'employee_id': employee_id.id,
                            'date': single_date,
                            'type': 'normal_time_off'
                        })
                if not absent_id:
                    shift_ids = employee_id.resource_calendar_id.attendance_ids.filtered(
                        lambda a: a.dayofweek == str(single_date.weekday()))
                    for shift_id in shift_ids:
                        morning_end_duration_obj = False
                        if shift_id.day_period == 'morning':
                            duration_str = '{0:02.0f}:{1:02.0f}:00'.format(*divmod(shift_id.hour_to * 60, 60))
                            morning_start_duration_obj = datetime.strptime('00:00:00', '%H:%M:00')
                            morning_start_duration_obj = morning_start_duration_obj.replace(year=single_date.year,
                                                                                            month=single_date.month,
                                                                                            day=single_date.day)
                            morning_start_duration_obj = morning_start_duration_obj.astimezone(tz=timezone(tz))
                            morning_end_duration_obj = datetime.strptime(duration_str, '%H:%M:00')
                            morning_end_duration_obj = morning_end_duration_obj.replace(year=single_date.year,
                                                                                        month=single_date.month,
                                                                                        day=single_date.day)
                            morning_end_duration_obj = morning_end_duration_obj.astimezone(tz=timezone(tz))
                            morning_domain = [
                                ('employee_id', '=', employee_id.id),
                                ('check_in', '>', morning_start_duration_obj),
                                ('check_in', '<', morning_end_duration_obj),
                            ]
                            morning_attendance_id = HrAttendance.search(morning_domain)
                            if not morning_attendance_id:
                                count += 1

                        elif shift_id.day_period == 'afternoon':
                            if morning_end_duration_obj:
                                noon_start_duration_obj = morning_end_duration_obj
                            else:
                                duration_str = '{0:02.0f}:{1:02.0f}:00'.format(*divmod(shift_id.hour_from * 60, 60))
                                noon_start_duration_obj = datetime.strptime(duration_str, '%H:%M:00')
                                noon_start_duration_obj = noon_start_duration_obj.replace(year=single_date.year,
                                                                                          month=single_date.month,
                                                                                          day=single_date.day)
                                noon_start_duration_obj = noon_start_duration_obj.astimezone(tz=timezone(tz))

                            noon_end_duration_obj = datetime.strptime('23:59:59', '%H:%M:59')
                            noon_end_duration_obj = noon_end_duration_obj.replace(year=single_date.year,
                                                                                  month=single_date.month,
                                                                                  day=single_date.day)
                            noon_end_duration_obj = noon_end_duration_obj.astimezone(tz=timezone(tz))
                            domain = [
                                ('employee_id', '=', employee_id.id),
                                '|',
                                ('check_in', '>', str(noon_start_duration_obj)),
                                ('check_in', '<', str(noon_end_duration_obj)),
                            ]
                            noon_attendance_id = HrAttendance.search(domain)
                            if not noon_attendance_id and not absent_id:
                                count += 1

        absent_ids.unlink()

        if count > 0:
            return count * amount_per_day * -1
        else:
            return 0.0

    def action_payslip_done(self):
        rules = []
        for line in self.loan_ids:
            if line.paid:
                if self.struct_id:
                    for line_id in self.struct_id.rule_ids:
                        rules.append(line_id.code)
                if 'LO' in rules:
                    line.action_paid_amount()
                else:
                    raise ValidationError(_("Add Salary rule for loan in salary structure"))
            else:
                line.payslip_id = False
        return super(HrPayslipAcc, self).action_payslip_done()
