# -*- coding: utf-8 -*-

from odoo import models, fields
from datetime import timedelta, datetime
import pytz
from odoo.addons.resource.models.resource import float_to_time

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
TIME_FORMAT = "%H:%M:%S"


class TransactionGenerateWizard(models.TransientModel):
    _name = "transaction.generate.wizard"
    _description = "Transaction Generate Wizard"

    employee_ids = fields.Many2many('hr.employee', string="Employee(s)")
    date_from = fields.Date(string='From Date')
    date_to = fields.Date(string='To Date')

    def generate_transaction(self):
        employees = self.employee_ids or self.env['hr.employee'].search([])
        dates_range = (self.date_to - self.date_from).days + 1
        for emp in employees:
            for n in range(dates_range):
                date = self.date_from + timedelta(n)
                transaction = self.env['attendance.transaction'].search([('date', '=', date),
                                                                         ('employee_id', '=', emp.id)])
                if not transaction:
                    self._create_transaction(emp, date)

    def _create_transaction(self, employee, date):
        attendance_transaction = self.env['attendance.transaction']
        dayofweek = str(date.weekday())
        shift_schedule = attendance_transaction._get_work_calender(employee, date)
        resource_calendar_id = shift_schedule.shift_type_id if shift_schedule else employee.contract_id.resource_calendar_id or employee.resource_calendar_id
        attendance_ids = resource_calendar_id.attendance_ids.filtered(lambda line: line.dayofweek == dayofweek)
        if not attendance_ids: attendance_ids = resource_calendar_id.attendance_ids[0]
        status = 'ab'
        attendance = self.env['hr.attendance'].search([('employee_id', '=', employee.id), ('is_taken', '=', False),
                                                       ('atten_date', '=', date)], order='check_in desc', limit=1)
        if attendance:
            tzinfo = pytz.timezone(attendance.employee_id.tz)
            ac_sign_out = 00.00
            check_in = attendance.check_in.astimezone(tzinfo)
            ac_sign_in = attendance_transaction._time_to_float(check_in) if resource_calendar_id.check_in_necessary == 'yes' else '00:02'
            status = 'ex'
            if attendance.check_out:
                check_out = attendance.check_out.astimezone(tzinfo)
                ac_sign_out = attendance_transaction._time_to_float(check_out)

            attendance_transaction.create({
                'date': attendance.atten_date,
                'atten_date': attendance.atten_date,
                'employee_id': employee.id,
                'attendance_id': attendance.id,
                'day': str(attendance.atten_date.weekday()),
                'ac_sign_in': ac_sign_in if resource_calendar_id.check_in_necessary == 'yes' else attendance_ids[0].hour_from,
                'ac_sign_out': ac_sign_out if resource_calendar_id.check_out_necessary == 'yes' else attendance_ids[0].hour_to,
                'pl_sign_in': attendance_ids[0].hour_from,
                'pl_sign_in_end': attendance_ids[0].check_in_end,
                'pl_sign_out': attendance_ids[0].hour_to,
                'pl_sign_out_start': attendance_ids[0].check_out_start,

                'status': status
            })

            if attendance.check_out:
                attendance_transaction.write({'is_taken': True, })
        else:
            status = 'ab'


            hour_from = float_to_time(float(attendance_ids[0].hour_from))
            date_from = datetime.combine(date, hour_from)
            holiday = attendance_transaction.get_public_holiday(date_from, employee)
            if len(holiday) > 0:
                status = 'ph'
            leaves = attendance_transaction._get_emp_leave_intervals(employee, date)
            if len(leaves) > 0:
                status = 'leave'
            if attendance_transaction._get_weekend_days(employee, date) or attendance_ids[0].is_weekend:
                status = 'weekend'
            

            attendance_transaction.create({
                'date': date,
                'employee_id': employee.id,
                'day': dayofweek,
                'ac_sign_in': 00.00 if resource_calendar_id.check_in_necessary == 'yes' else attendance_ids[0].hour_from,
                'ac_sign_out': 00.00 if resource_calendar_id.check_out_necessary == 'yes' else attendance_ids[0].hour_to,
                'pl_sign_in': attendance_ids[0].hour_from if attendance_ids else 0.0,
                'pl_sign_in_end': attendance_ids[0].check_in_end if attendance_ids else 0.0,
                'pl_sign_out': attendance_ids[0].hour_to if attendance_ids else 0.0,
                'pl_sign_out_start': attendance_ids[0].check_out_start if attendance_ids else 0.0,
                'status': 'ex' if (resource_calendar_id.check_in_necessary == 'no' or resource_calendar_id.check_out_necessary == 'no') and status == 'ab' else status,
            })




