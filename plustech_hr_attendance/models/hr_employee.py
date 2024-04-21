# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time


class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    ded_days = fields.Float(string='Days Deduction')
    allowed_late_hours = fields.Float(string='Maximum Allowed Late Hours')

    @api.model
    def compute_absent_days(self):
        for rec in self.env['hr.employee'].search([('calendar_id.check_in_necessary', '=', 'yes')]):
        # for rec in self:
        #     if rec.calendar_id.check_in_necessary == 'yes':
            date_now = fields.date.today().strftime(DEFAULT_SERVER_DATE_FORMAT)
            start_month = time.strftime('%Y-%m-01')
            first_attendance = False
            last_attendance = False
            start_month = datetime.strptime(start_month, DEFAULT_SERVER_DATE_FORMAT).date()
            date_now = datetime.strptime(date_now, DEFAULT_SERVER_DATE_FORMAT).date()
            attendance_ded = self.env['hr.attendance'].search(
                [('employee_id', '=', rec.id), ('attendance_date', '>=', start_month)], order='attendance_date ASC')
            print(attendance_ded)
            if len(attendance_ded) > 1:
                first_attendance = attendance_ded[0].attendance_date
                last_attendance = attendance_ded[-1].attendance_date
                leaves_from = self.env['hr.holidays'].search([('employee_id', '=', rec.id),
                                                              ('type', '=', 'remove'),
                                                              ('state', '=', 'validate')])
                days_ded = 0.0
                public_leave = 0.0
                if first_attendance:
                    first_attendance = datetime.strptime(first_attendance, DEFAULT_SERVER_DATE_FORMAT).date()
                if last_attendance:
                    last_attendance = datetime.strptime(last_attendance, DEFAULT_SERVER_DATE_FORMAT).date()
                if leaves_from:
                    for leave in leaves_from:
                        leave_date_from = datetime.strptime(str(leave.date_from), "%Y-%m-%d %H:%M:%S").date()
                        leave_date_to = datetime.strptime(str(leave.date_to), "%Y-%m-%d %H:%M:%S").date()
                        if first_attendance > date_now or last_attendance < date_now:
                            print(leave_date_from, start_month, date_now)
                            if start_month <= leave_date_from <= date_now:
                                days_first = (first_attendance - start_month).days
                                days = (leave_date_to - leave_date_from).days - 1
                                days_last = (date_now - last_attendance).days
                                days_ded = (days_last + days_first - days) - rec.ded_days
                            if leave_date_from <= start_month <= leave_date_to:
                                days_first = (first_attendance - start_month).days
                                days = (leave_date_to - start_month).days
                                days_last = (date_now - last_attendance).days - 1
                                days_ded = (days_last + days_first - days) - rec.ded_days
                            if leave_date_from >= start_month and leave_date_to >= date_now:
                                days_first = (first_attendance - start_month).days
                                days = (date_now - leave_date_from).days - 1
                                days_last = (date_now - last_attendance).days
                                days_ded = (days_last + days_first - days) - rec.ded_days
                if not leaves_from:
                    print(first_attendance,last_attendance)
                    days_first = (first_attendance - start_month).days
                    days_last = (date_now - last_attendance).days
                    days_ded = (days_last + days_first) - rec.ded_days
                    print(days_ded,'DAYS')

            else:
                days_ded = (date_now - start_month).days
            if rec.calendar_id.leave_ids:
                for public_leave in rec.calendar_id.leave_ids:
                    leave_date_from = datetime.strptime(str(public_leave.date_from), "%Y-%m-%d %H:%M:%S").date()
                    leave_date_to = datetime.strptime(str(public_leave.date_to), "%Y-%m-%d %H:%M:%S").date()
                    if start_month <= leave_date_from <= date_now:
                        public_leave = (leave_date_to - leave_date_from).days
                    if leave_date_from <= start_month <= leave_date_to:
                        public_leave = (leave_date_to - start_month).days
                    if leave_date_from >= start_month and leave_date_to >= date_now:
                        public_leave = (date_now - leave_date_from).days
            rec.ded_days = days_ded - public_leave


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'
    ded_days = fields.Float(string='Days Deduction')
    allowed_late_hours = fields.Float(string='Maximum Allowed Late Hours')

