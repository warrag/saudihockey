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
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import pytz

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
TIME_FORMAT = "%H:%M:%S"


class AttendanceTransaction(models.Model):
    _inherit = 'attendance.transaction'

    overtime = fields.Float("Overtime", readonly=True, compute='compute_check_diff')
    overtime_amount = fields.Float("Overtime Amount", readonly=True, compute='compute_check_diff')

    @api.depends('employee_id', 'ac_sign_in', 'ac_sign_out')
    def compute_check_diff(self):

        for rec in self:
            rec.overtime_amount = 0.0
            rec.overtime = 0.0
            shift_calender = self._get_work_calender(rec.employee_id, rec.date)
            calendar_id = shift_calender.shift_type_id if shift_calender else rec.employee_id.contract_id.resource_calendar_id
            if rec.employee_id and rec.ac_sign_in:
                check_in_ot_diff = 0.0
                check_out_ot_diff = 0.0
                work_days = []
                wage = rec.employee_id.contract_id.wage
                attendance_date = datetime.strptime(str(rec.date),
                                                    DEFAULT_SERVER_DATE_FORMAT).date()
                attendance_ids = self.env['hr.attendance'].search([('atten_date', '=', attendance_date)],
                                                                  order='check_in ASC')
                if attendance_ids:
                    if rec.ac_sign_in != attendance_ids[0].check_in:
                        schedule_id = self.env['resource.calendar.attendance'].search(
                            [('calendar_id', '=', calendar_id.id),
                             ('dayofweek', '=', str(attendance_date.weekday()))]
                            , order='hour_from DESC', limit=1)
                    else:
                        schedule_id = self.env['resource.calendar.attendance'].search(
                            [('calendar_id', '=', calendar_id.id),
                             ('dayofweek', '=', str(attendance_date.weekday()))]
                            , order='hour_from ASC', limit=1)
                else:
                    schedule_id = self.env['resource.calendar.attendance'].search(
                        [('calendar_id', '=', calendar_id.id),
                         ('dayofweek', '=', str(attendance_date.weekday()))]
                        , order='hour_from ASC', limit=1)
                atten_date = datetime.combine(rec.date, datetime.min.time())
                ac_sign_in = atten_date + timedelta(hours=rec.ac_sign_in)
                check_in_date = datetime.strptime(str(ac_sign_in), DEFAULT_SERVER_DATETIME_FORMAT).date()
                check_in = datetime.strptime(str(ac_sign_in), DEFAULT_SERVER_DATETIME_FORMAT) + relativedelta(
                    hours=3)
                if schedule_id:
                    wage_minute = wage / (schedule_id.calendar_id.month_work_days * schedule_id.calendar_id.work_hours)
                    schedule_start_in = str(check_in_date) + ' ' + schedule_id.check_in_start_str
                    schedule_check_in = str(check_in_date) + ' ' + schedule_id.check_in_str
                    schedule_end_in = str(check_in_date) + ' ' + schedule_id.check_in_end_str
                    schedule_check_in = datetime.strptime(schedule_check_in, DEFAULT_SERVER_DATETIME_FORMAT)
                    schedule_start_in = datetime.strptime(schedule_start_in, DEFAULT_SERVER_DATETIME_FORMAT)
                    schedule_end_in = datetime.strptime(schedule_end_in, DEFAULT_SERVER_DATETIME_FORMAT)

                    if schedule_id.calendar_id.attendance_ids:
                        for attendance in schedule_id:
                            work_days.append(str(attendance.dayofweek))

                if schedule_id and rec.ac_sign_in:
                    if check_in < schedule_start_in:
                        if schedule_id.calendar_id.check_in_early == 'yes':
                            check_in_ot_diff = ((schedule_start_in - check_in).total_seconds() / 60)
                            if check_in_ot_diff < float(schedule_id.calendar_id.min_ot_check_in):
                                check_in_ot_diff = 0.0

                if rec.ac_sign_out and schedule_id:
                    atten_date = datetime.combine(rec.date, datetime.min.time())
                    ac_sign_out = atten_date + timedelta(hours=rec.ac_sign_out)
                    check_out = datetime.strptime(str(ac_sign_out), DEFAULT_SERVER_DATETIME_FORMAT) + relativedelta(
                        hours=3)
                    schedule_end_out = str(atten_date.date()) + ' ' + schedule_id.check_out_end_str
                    schedule_end_out = datetime.strptime(schedule_end_out, DEFAULT_SERVER_DATETIME_FORMAT)

                    if check_out > schedule_end_out:
                        if schedule_id.calendar_id.check_out_delay == 'yes':
                            check_out_ot_diff = (check_out - schedule_end_out).total_seconds() / 3600
                            if (check_out_ot_diff * 60) < schedule_id.calendar_id.min_ot_check_out:
                                check_out_ot_diff = 0.0
                if check_in_ot_diff >= 0.0 and check_out_ot_diff >= 0.0:
                    minute_wage = rec.employee_id.contract_id.over_hour / 60
                    if str(check_in_date.weekday()) in work_days:
                        rec.overtime = (check_in_ot_diff * schedule_id.calendar_id.ot_working_day) + \
                                       (check_out_ot_diff * schedule_id.calendar_id.ot_working_day)
                        rec.overtime_amount = (
                                                      check_in_ot_diff * minute_wage * schedule_id.calendar_id.ot_working_day) + \
                                              (check_out_ot_diff * minute_wage * schedule_id.calendar_id.ot_working_day)
                    if str(check_in_date.weekday()) not in work_days:
                        rec.overtime = (check_in_ot_diff * schedule_id.calendar_id.ot_holiday) + \
                                       (check_out_ot_diff * schedule_id.calendar_id.ot_holiday)
                        rec.overtime_amount = (check_in_ot_diff * minute_wage * schedule_id.calendar_id.ot_holiday) + \
                                              (check_out_ot_diff * minute_wage * schedule_id.calendar_id.ot_holiday)
