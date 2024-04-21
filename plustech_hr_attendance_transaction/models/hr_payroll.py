# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    att_date_from = fields.Date('Att Date From')
    att_date_to = fields.Date('Att Date To')

    @api.onchange('date_start', 'date_end')
    def _onchange_att_date_from(self):
        self.att_date_from = self.date_start
        self.att_date_to = self.date_end

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    attendance_ded = fields.Float(string='Attendance Month Deduction', compute='compute_attendance_ded')

    att_date_from = fields.Date('Att Date From', related='payslip_run_id.att_date_from')
    att_date_to = fields.Date('Att Date To', related='payslip_run_id.att_date_to')

    @api.depends('employee_id', 'att_date_from', 'att_date_to')
    def compute_attendance_ded(self):
        for slip in self:

            total_ded = 0.0
            attendance_ded = self.env['attendance.transaction'].search(
                [('employee_id', '=', slip.employee_id.id), ('date', '>=', slip.att_date_from),
                 ('date', '<=', slip.att_date_to), ('status', 'in', ['ex', 'ab']),
                 ('diff_time', '!=', 0), ('deducted_amount', '!=', 0.0)], order='date ASC')
            
            deducted_amount = sum(abs(line.deducted_amount) for line in attendance_ded)
            hours = (sum(abs(line.diff_time) for line in attendance_ded)) - slip.employee_id.allowed_late_hours
            allowance_ids = slip.employee_id.contract_id.allowance_ids.filtered(lambda al: al.allowance_type.attendance_deduction)
            wage = slip.employee_id.contract_id.wage + sum(allowance_ids.mapped('allowance_amount'))

            if slip.employee_id.allowed_late_hours == 0:
                total_ded = deducted_amount
        

            elif hours > 0:
                shift_calender = self.env['attendance.transaction']._get_work_calender(slip.employee_id, slip.att_date_from)
                schedule_id = shift_calender.shift_type_id if shift_calender else slip.contract_id.resource_calendar_id
                hours_per_day = schedule_id.hours_per_day if schedule_id.hours_per_day > 0 else 8
                minute_wage = (wage / 30) / hours_per_day / 60 or 0.0
                deducted_minutes = (hours * 60) * schedule_id.check_out_minute
                total_ded = abs(deducted_minutes) * minute_wage
            slip.attendance_ded = total_ded
