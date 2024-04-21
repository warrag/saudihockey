# -*- coding: utf-8 -*-

##############################################################################
#
#
#    Copyright (C) 2020-TODAY .
#    Author: Eng.Hassan Abdallah
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
##############################################################################

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.addons.resource.models.resource import float_to_time
import pytz

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
TIME_FORMAT = "%H:%M:%S"


class AttendanceTransaction(models.Model):
    _name = 'attendance.transaction'
    _description = 'Hr Attendance Transaction'
    _order = 'date desc'

    employee_id = fields.Many2one(comodel_name='hr.employee', string='Employee',
                                  required=True)
    attendance_id = fields.Many2one('hr.attendance')
    leave_id = fields.Many2one('hr.leave', compute='compute_leave', store=True, index=True)
    public_holiday_id = fields.Many2one('resource.calendar.leaves', compute='compute_public_holiday',
                                        store=True, index=True)
    deputation_id = fields.Many2one('hr.deputation')
    department_id = fields.Many2one(related='employee_id.department_id',
                                    string='Department', store=True)
    date = fields.Date("Date")
    atten_date = fields.Date("Atten Date")
    day = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ], 'Day of Week', required=True, index=True, )
    pl_sign_in = fields.Float("Planned sign in", readonly=True)
    pl_sign_in_end = fields.Float("Planned Sign-In End", readonly=True)
    pl_sign_out = fields.Float("Planned sign out", readonly=True)
    pl_sign_out_start = fields.Float("Planned Sign-Out Start", readonly=True)
    pl_hours = fields.Float("Working Hours", compute="compute_working_hours", store=True, readonly=True)
    pl_hours_display = fields.Char("PL/Hours", default='00:00')
    worked_hours = fields.Char("Worked Hours", compute="compute_working_hours", default='00:00',
                               store=True, readonly=True)
    ac_sign_in = fields.Float("Actual sign in", readonly=True)
    ac_sign_in_display = fields.Char("Actual sign in", compute="_compute_time_to_display")
    ac_sign_out = fields.Float("Actual sign out", readonly=True)
    ac_sign_out_display = fields.Char("Actual sign out", compute="_compute_time_to_display")
    # overtime = fields.Float("Overtime", readonly=True, compute='compute_check_diff')
    # overtime_amount = fields.Float("Overtime Amount", readonly=True, compute='compute_check_diff')
    late_in = fields.Float("Early late", readonly=True, compute='_compute_early_late', store=True)
    late_in_display = fields.Char("Early late", default='00:00', readonly=True)
    diff_time = fields.Float("Diff Time", compute="_compute_diff_time", store=True,
                             help="Difference between the working time and attendance time(s) ",
                             readonly=True)
    diff_time_display = fields.Char("Diff Time", compute="_compute_diff_time", store=True,
                                    help="Difference between the working time and attendance time(s) ",
                                    readonly=True)
    deducted_amount = fields.Float(compute="_compute_deducted_amount", store=True, readonly=True)
    early_exit = fields.Float("Early Exit", readonly=True, compute='_compute_early_exit', store=True)
    early_exit_display = fields.Char("Early Exit", default="00:00", readonly=True)

    permission_time = fields.Float("Permission Time", readonly=True, compute='_compute_permission_time', store=True)
    permission_time_display = fields.Char("Permission Time", default="00:00", readonly=True)

    status = fields.Selection(string="Status",
                              selection=[('ex', 'Exist'),
                                         ('ab', 'Absence'),
                                         ('weekend', 'Week End'),
                                         ('ph', 'Public Holiday'),
                                         ('leave', 'Leave'),
                                         ('dep', 'Deputation'), ],
                              required=False, readonly=True)
    company_id = fields.Many2one('res.company', 'Company', related='employee_id.company_id')

    @api.depends('employee_id', 'date')
    def compute_leave(self):
        for rec in self:
            leave_id = False
            leaves = self._get_emp_leave_intervals(rec.employee_id, rec.date)
            if leaves:
                leave_id = leaves[0].id
            rec.leave_id = leave_id

    @api.depends('employee_id', 'date')
    def compute_public_holiday(self):
        for rec in self:
            holiday = False
            shift_schedule = self._get_work_calender(rec.employee_id, rec.date)
            resource_calendar_id = shift_schedule.shift_type_id if shift_schedule else rec.employee_id.contract_id.resource_calendar_id or rec.employee.resource_calendar_id
            attendance_ids = resource_calendar_id.attendance_ids.filtered(lambda line: line.dayofweek == str(rec.date.weekday()))
            hour_from = float_to_time(float(attendance_ids[0].hour_from))
            date_from = datetime.combine(rec.date, hour_from)
            holidays = self.get_public_holiday(date_from, rec.employee_id)
            if holidays:
                holiday = holidays[0].id
            rec.public_holiday_id = holiday

    @api.depends('ac_sign_in', 'ac_sign_out')
    def _compute_permission_time(self):
        for rec in self:
            permissions = self.env['hr.leave'].search([('employee_id', '=', rec.employee_id.id), 
                                                       ('request_date_from', '=', rec.date),
                                                       ('holiday_status_id.is_permission', '=', True),
                                                       ('holiday_status_id.request_unit', '=', 'hour'),
                                                       ('state', 'not in', ['draft', 'confirm', 'refuse'])])

            if permissions:
                rec.permission_time = sum(permissions.mapped('number_of_hours_display'))
                rec.permission_time_display = self._float_to_time(rec.permission_time)

    @api.depends('ac_sign_in', 'ac_sign_out')
    def _compute_time_to_display(self):
        for record in self:
            record.ac_sign_in_display = self._float_to_time(record.ac_sign_in)
            record.ac_sign_out_display = self._float_to_time(record.ac_sign_out)

    def _get_work_calender(self, employee, date):
        shift_domain = [('start_date', '<=', date),
                        ('end_date', '>=', date)]
        shift_schedule = self.env['hr.employee.shift'].search(
            [('employee_id', '=', employee.id), ('shift_mode', '=', 'employee')] + shift_domain) or \
                         self.env['hr.employee.shift'].search([('department_id', '=', employee.department_id.id),
                                                               ('shift_mode', '=', 'department')] + shift_domain) or \
                         self.env['hr.employee.shift'].search(
                             [('company_id', '=', employee.company_id.id),
                              ('shift_mode', '=', 'company')] + shift_domain)
        return shift_schedule

    def _time_to_float(self, time_object):
        time_str = time_object.strftime("%H:%M")
        hours, minutes = map(float, time_str.split(':'))
        seconds = 0
        time_float = hours + minutes / 60 + seconds / 3600
        return time_float

    def _float_to_time(self, value):
        str_time = '{0:02.0f}:{1:02.0f}'.format(*divmod(abs(value) * 60, 60))
        return str_time

    @api.model
    def _get_attendance_transaction(self):
        attendance_transaction = self.env['attendance.transaction']
        employee_obj = self.env['hr.employee'].search([])
        today = fields.Date.today()
        now = datetime.now()
        for emp in employee_obj:
            
            attendance = self.env['hr.attendance'].search(
                [('employee_id', '=', emp.id), ('is_taken', '=', False)], order='check_in desc')
            for atten in attendance:
                dayofweek = str(atten.atten_date.weekday())
                shift_schedule = self._get_work_calender(emp, atten.atten_date)
                resource_calendar_id = shift_schedule.shift_type_id if shift_schedule else emp.contract_id.resource_calendar_id or emp.resource_calendar_id
                attendance_ids = resource_calendar_id.attendance_ids.filtered(lambda line: line.dayofweek == dayofweek)
                if not attendance_ids:
                    attendance_ids = resource_calendar_id.attendance_ids[0]
                
                tzinfo = pytz.timezone(atten.employee_id.tz)
                transaction = attendance_transaction.search(
                    [('employee_id', '=', emp.id),  '|', ('attendance_id', '=', atten.id),
                     ('date', '=', atten.atten_date)])
                ac_sign_in = 00.00
                ac_sign_out = 00.00
                if atten:
                    check_in = atten.check_in.astimezone(tzinfo)
                    ac_sign_in = self._time_to_float(check_in)
                    status = 'ex'
                if atten.check_out:
                    check_out = atten.check_out.astimezone(tzinfo)
                    ac_sign_out = self._time_to_float(check_out)

                if len(transaction) == 0:
                    attendance_transaction.create({
                        'date': atten.atten_date,
                        'atten_date': atten.atten_date,
                        'employee_id': emp.id,
                        'attendance_id': atten.id,
                        'day': str(atten.atten_date.weekday()),
                        'ac_sign_in': ac_sign_in,
                        'ac_sign_out': ac_sign_out,
                        'pl_sign_in': attendance_ids[0].hour_from,
                        'pl_sign_in_end': attendance_ids[0].check_in_end,
                        'pl_sign_out': attendance_ids[0].hour_to,
                        'pl_sign_out_start': attendance_ids[0].check_out_start,
                        'status': status
                    })
                elif len(transaction) > 0:
                    transaction.write({
                        'ac_sign_out': ac_sign_out,
                        'ac_sign_in': ac_sign_in,
                        'status': status,
                        'attendance_id': atten.id
                    })
                if atten.check_out:
                    atten.write({'is_taken': True, })

            dayofweek = str(today.weekday())
            shift_schedule = self._get_work_calender(emp, today)
            resource_calendar_id = shift_schedule.shift_type_id if shift_schedule else emp.contract_id.resource_calendar_id or emp.resource_calendar_id
            attendance_ids = resource_calendar_id.attendance_ids.filtered(lambda line: line.dayofweek == dayofweek)
            if not attendance_ids:
                attendance_ids = resource_calendar_id.attendance_ids[0]
            status = 'ab'

            today_checkin = self.env['hr.attendance'].search(
                [('employee_id', '=', emp.id), ('atten_date', '=', today)], order='check_out asc')
            today_trans = attendance_transaction.search([('employee_id', '=', emp.id), ('date', '=', today)], limit=1)
            if len(today_checkin) == 0 and len(today_trans) == 0:
                status = 'ab'
                holiday = self.get_public_holiday(now, emp)
                if len(holiday) > 0:
                    status = 'ph'
                leaves = self._get_emp_leave_intervals(emp, today)
                if len(leaves) > 0:
                    status = 'leave'
                if self._get_weekend_days(emp, today) or attendance_ids[0].is_weekend:
                    status = 'weekend'
                attendance_transaction.create({
                    'date': today,
                    'employee_id': emp.id,
                    'day': str(today.weekday()),
                    'ac_sign_in': 00.00 if resource_calendar_id.check_in_necessary == 'yes' else attendance_ids[0].hour_from,
                    'ac_sign_out': 00.00 if resource_calendar_id.check_out_necessary == 'yes' else attendance_ids[0].hour_to,
                    'pl_sign_in': attendance_ids[0].hour_from if attendance_ids else 0.0,
                    'pl_sign_in_end': attendance_ids[0].check_in_end if attendance_ids else 0.0,
                    'pl_sign_out': attendance_ids[0].hour_to if attendance_ids else 0.0,
                    'pl_sign_out_start': attendance_ids[0].check_out_start if attendance_ids else 0.0,
                    'status': 'ex' if (resource_calendar_id.check_in_necessary == 'no' or resource_calendar_id.check_out_necessary == 'no') and status == 'ab' else status,

                })

    def _get_emp_leave_intervals(self, emp, start_datetime=None):
        leave_obj = self.env['hr.leave']
        leave_ids = leave_obj.search([
            ('employee_id', '=', emp.id),
            ('state', '=', 'validate'),
            ('date_from', '<=', start_datetime),
            ('date_to', '>=', start_datetime)
        ])

        return leave_ids

    def get_public_holiday(self, date, emp):
        shift_calender = self._get_work_calender(emp, date)
        calendar_id = shift_calender.shift_type_id if shift_calender else emp.contract_id.resource_calendar_id
        holiday = calendar_id.global_leave_ids.filtered(lambda line: line.date_from <= date and line.date_to >= date)
        return holiday

    def _get_weekend_days(self, employee_id, date):
        weekend = False
        shift_calender = self._get_work_calender(employee_id, date)
        Working_Hours = shift_calender.shift_type_id if shift_calender else employee_id.contract_id.resource_calendar_id
        attendance = Working_Hours.attendance_ids
        work_day = []
        for attend in attendance:
            if attend.dayofweek not in work_day:
                work_day.append(attend.dayofweek)
        if str(date.weekday()) not in work_day:
            weekend = True
        return weekend

    @api.depends('pl_sign_in_end', 'ac_sign_in')
    def _compute_early_late(self):
        for rec in self:
            shift_calender = self._get_work_calender(rec.employee_id, rec.date)
            working_calendar_id = shift_calender.shift_type_id if shift_calender else rec.employee_id.contract_id.resource_calendar_id
            if rec.pl_sign_in_end and rec.ac_sign_in:
                if rec.ac_sign_in > rec.pl_sign_in_end:
                    late_in = rec.ac_sign_in - rec.pl_sign_in
                    rec.late_in = late_in if late_in > 0 else 0
                    rec.late_in_display = self._float_to_time(rec.late_in)
                else:
                    late_in = rec.ac_sign_in - rec.pl_sign_in_end
                    rec.late_in = late_in if late_in > 0 else 0
                    rec.late_in_display = self._float_to_time(rec.late_in)
                if rec.status == 'ex' and (rec.late_in * 60) > 0 and working_calendar_id.check_in_late > 0:
                    rec.status = 'ab'
                if rec.ac_sign_in == 0 and rec.status == 'ex':
                    if working_calendar_id.no_ckeck_in == 'absent':
                        rec.status = 'ab'
                    elif working_calendar_id.no_ckeck_in == 'late':
                        rec.late_in = working_calendar_id.no_check_in_minute/60 if working_calendar_id.no_check_in_minute < 0 else 0.0

    @api.depends('pl_sign_out_start', 'ac_sign_out')
    def _compute_early_exit(self):
        for rec in self:
            shift_calender = self._get_work_calender(rec.employee_id, rec.date)
            working_calendar_id = shift_calender.shift_type_id if shift_calender else rec.employee_id.contract_id.resource_calendar_id
            if rec.pl_sign_out_start and rec.ac_sign_out:
                if rec.ac_sign_out > rec.pl_sign_out_start:
                    early_exit = rec.ac_sign_out - rec.pl_sign_out_start
                    rec.early_exit = early_exit if early_exit < 0 else 0
                    rec.early_exit_display = self._float_to_time(rec.early_exit)
                else:
                    early_exit = rec.ac_sign_out - rec.pl_sign_out_start
                    rec.early_exit = early_exit if early_exit < 0 else 0
                    rec.early_exit_display = self._float_to_time(rec.early_exit)

                if rec.status == 'ex' and (rec.early_exit * 60) > 0 and working_calendar_id.check_out_early > 0:
                    rec.status = 'ab'
                if rec.ac_sign_out == 0 and rec.status == 'ex':
                    if working_calendar_id.no_check_out == 'absent':
                        rec.status = 'ab'
                    elif working_calendar_id.no_ckeck_out == 'late':
                        rec.late_in = working_calendar_id.no_check_out_minute/60 if working_calendar_id.no_check_out_minute < 0 else 0.0

    @api.depends('late_in', 'early_exit')
    def _compute_diff_time(self):
        for rec in self:
            is_weekend = rec.employee_id.resource_calendar_id.attendance_ids.filtered(lambda line: line.dayofweek == str(rec.date.weekday())).is_weekend
            leaves = rec._get_emp_leave_intervals(rec.employee_id, rec.date)

            if rec.late_in or rec.early_exit:
                rec.diff_time = ((abs(rec.late_in) + abs(rec.early_exit)) - abs(rec.permission_time))
            elif not rec.ac_sign_in:
                rec.diff_time = -rec.pl_hours
            elif rec.diff_time < 0 or is_weekend:
                rec.diff_time = 0.0
            if rec.status == 'ab':
                rec.diff_time = rec.employee_id.resource_calendar_id.hours_per_day
            
            if len(leaves) > 0:
                rec.diff_time = 0.0 

            rec.diff_time_display = self._float_to_time(rec.diff_time)

    @api.depends('ac_sign_in', 'ac_sign_out')
    def compute_working_hours(self):
        for rec in self:
            if rec.ac_sign_in and rec.ac_sign_out:
                worked_hours = rec.ac_sign_out - rec.ac_sign_in
                rec.worked_hours = self._float_to_time(worked_hours)
            if rec.pl_sign_in and rec.pl_sign_out:
                rec.pl_hours = rec.pl_sign_out - rec.pl_sign_in
                rec.pl_hours_display = self._float_to_time(rec.pl_hours)

    @api.depends('diff_time', 'late_in', 'early_exit')
    def _compute_deducted_amount(self):
        for rec in self:
            rec.deducted_amount = 0
            if rec.status in ('ab','ex'):
                shift_calender = self._get_work_calender(rec.employee_id, rec.date)
                schedule_id = shift_calender.shift_type_id if shift_calender else rec.employee_id.contract_id.resource_calendar_id
                is_weekend = rec.employee_id.resource_calendar_id.attendance_ids.filtered(lambda line: line.dayofweek == str(rec.date.weekday())).is_weekend
                leaves = rec._get_emp_leave_intervals(rec.employee_id, rec.date)

                deducted_minutes = 0.0
                if rec.late_in or rec.early_exit:
                    allow_late_in = rec.pl_sign_in_end - rec.pl_sign_in
                    if abs(rec.late_in) > allow_late_in:
                        late_in_deduct = (rec.late_in * 60) * schedule_id.check_in_minute
                        deducted_minutes += abs(late_in_deduct)
                    allow_early_exit = rec.pl_sign_out - rec.pl_sign_out_start
                    if abs(rec.early_exit) > allow_early_exit:
                        early_exit_deduct = (rec.early_exit * 60) * schedule_id.check_out_minute
                        deducted_minutes += abs(early_exit_deduct)
                elif rec.diff_time:
                    deducted_minutes = abs(rec.diff_time) * 60

                if rec.permission_time:
                    deducted_minutes -= rec.permission_time * 60
                if is_weekend:
                    deducted_minutes = 0.0
                if len(leaves) > 0:
                    deducted_minutes = 0.0 
                allowance_ids = rec.employee_id.contract_id.allowance_ids.filtered(lambda al: al.allowance_type.attendance_deduction)
                wage = rec.employee_id.contract_id.wage + sum(allowance_ids.mapped('allowance_amount'))
                minute_wage = (wage / 30) / schedule_id.hours_per_day / 60 or 0
                rec.deducted_amount = ((abs(deducted_minutes) * minute_wage)) if deducted_minutes > 0 else 0

    # @api.depends('employee_id', 'ac_sign_in', 'ac_sign_out')
    # def compute_check_diff(self):
    #
    #     for rec in self:
    #         rec.overtime_amount = 0.0
    #         rec.overtime = 0.0
    #         shift_calender = self._get_work_calender(rec.employee_id, rec.date)
    #         calendar_id = shift_calender.shift_type_id if shift_calender else rec.employee_id.contract_id.resource_calendar_id
    #         if rec.employee_id and rec.ac_sign_in:
    #             check_in_ot_diff = 0.0
    #             check_out_ot_diff = 0.0
    #             work_days = []
    #             wage = rec.employee_id.contract_id.wage
    #             attendance_date = datetime.strptime(str(rec.date),
    #                                                 DEFAULT_SERVER_DATE_FORMAT).date()
    #             attendance_ids = self.env['hr.attendance'].search([('atten_date', '=', attendance_date)],
    #                                                               order='check_in ASC')
    #             if attendance_ids:
    #                 if rec.ac_sign_in != attendance_ids[0].check_in:
    #                     schedule_id = self.env['resource.calendar.attendance'].search(
    #                         [('calendar_id', '=', calendar_id.id),
    #                          ('dayofweek', '=', str(attendance_date.weekday()))]
    #                         , order='hour_from DESC', limit=1)
    #                 else:
    #                     schedule_id = self.env['resource.calendar.attendance'].search(
    #                         [('calendar_id', '=', calendar_id.id),
    #                          ('dayofweek', '=', str(attendance_date.weekday()))]
    #                         , order='hour_from ASC', limit=1)
    #             else:
    #                 schedule_id = self.env['resource.calendar.attendance'].search(
    #                     [('calendar_id', '=', calendar_id.id),
    #                      ('dayofweek', '=', str(attendance_date.weekday()))]
    #                     , order='hour_from ASC', limit=1)
    #             atten_date = datetime.combine(rec.date, datetime.min.time())
    #             ac_sign_in = atten_date + timedelta(hours=rec.ac_sign_in)
    #             check_in_date = datetime.strptime(str(ac_sign_in), DEFAULT_SERVER_DATETIME_FORMAT).date()
    #             check_in = datetime.strptime(str(ac_sign_in), DEFAULT_SERVER_DATETIME_FORMAT) + relativedelta(
    #                 hours=3)
    #             if schedule_id:
    #                 wage_minute = wage / (schedule_id.calendar_id.month_work_days * schedule_id.calendar_id.work_hours)
    #                 schedule_start_in = str(check_in_date) + ' ' + schedule_id.check_in_start_str
    #                 schedule_check_in = str(check_in_date) + ' ' + schedule_id.check_in_str
    #                 schedule_end_in = str(check_in_date) + ' ' + schedule_id.check_in_end_str
    #                 schedule_check_in = datetime.strptime(schedule_check_in, DEFAULT_SERVER_DATETIME_FORMAT)
    #                 schedule_start_in = datetime.strptime(schedule_start_in, DEFAULT_SERVER_DATETIME_FORMAT)
    #                 schedule_end_in = datetime.strptime(schedule_end_in, DEFAULT_SERVER_DATETIME_FORMAT)
    #
    #                 if schedule_id.calendar_id.attendance_ids:
    #                     for attendance in schedule_id:
    #                         work_days.append(str(attendance.dayofweek))
    #
    #             if schedule_id and rec.ac_sign_in:
    #                 if check_in < schedule_start_in:
    #                     if schedule_id.calendar_id.check_in_early == 'yes':
    #                         check_in_ot_diff = ((schedule_start_in - check_in).total_seconds() / 60)
    #                         if check_in_ot_diff < float(schedule_id.calendar_id.min_ot_check_in):
    #                             check_in_ot_diff = 0.0
    #
    #             if rec.ac_sign_out and schedule_id:
    #                 atten_date = datetime.combine(rec.date, datetime.min.time())
    #                 ac_sign_out = atten_date + timedelta(hours=rec.ac_sign_out)
    #                 check_out = datetime.strptime(str(ac_sign_out), DEFAULT_SERVER_DATETIME_FORMAT) + relativedelta(
    #                     hours=3)
    #                 schedule_end_out = str(atten_date.date()) + ' ' + schedule_id.check_out_end_str
    #                 schedule_end_out = datetime.strptime(schedule_end_out, DEFAULT_SERVER_DATETIME_FORMAT)
    #
    #                 if check_out > schedule_end_out:
    #                     if schedule_id.calendar_id.check_out_delay == 'yes':
    #                         check_out_ot_diff = (check_out - schedule_end_out).total_seconds() / 3600
    #                         if (check_out_ot_diff * 60) < schedule_id.calendar_id.min_ot_check_out:
    #                             check_out_ot_diff = 0.0
    #             if check_in_ot_diff >= 0.0 and check_out_ot_diff >= 0.0:
    #                 minute_wage = rec.employee_id.contract_id.over_hour / 60
    #                 if str(check_in_date.weekday()) in work_days:
    #                     rec.overtime = (check_in_ot_diff * schedule_id.calendar_id.ot_working_day) + \
    #                                    (check_out_ot_diff * schedule_id.calendar_id.ot_working_day)
    #                     rec.overtime_amount = (
    #                                                   check_in_ot_diff * minute_wage * schedule_id.calendar_id.ot_working_day) + \
    #                                           (check_out_ot_diff * minute_wage * schedule_id.calendar_id.ot_working_day)
    #                 if str(check_in_date.weekday()) not in work_days:
    #                     rec.overtime = (check_in_ot_diff * schedule_id.calendar_id.ot_holiday) + \
    #                                    (check_out_ot_diff * schedule_id.calendar_id.ot_holiday)
    #                     rec.overtime_amount = (check_in_ot_diff * minute_wage * schedule_id.calendar_id.ot_holiday) + \
    #                                           (check_out_ot_diff * minute_wage * schedule_id.calendar_id.ot_holiday)

    def unlink(self):
        if self.attendance_id:
            self.attendance_id.is_taken = False
        return super(AttendanceTransaction, self).unlink()


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'
    atten_date = fields.Date(compute='_get_attendance', store=True)
    is_taken = fields.Boolean()

    @api.depends('check_in')
    def _get_attendance(self):
        for rec in self:
            rec.atten_date = rec.check_in.strftime('%Y-%m-%d')
