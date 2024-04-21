# -*- coding: utf-8 -*-

from odoo import _, fields, models, api
from datetime import timedelta

MONTHS = [('1', 'January'), ('2', 'February'), ('3', 'March'),
          ('4', 'April'), ('5', 'May'), ('6', 'June'), ('7', 'July'),
          ('8', 'August'), ('9', 'September'), ('10', 'October'),
          ('11', 'November'), ('12', 'December')]


class AttendanceReportWizard(models.TransientModel):
    _name = 'attendance.report.wizard'
    _description = 'Employee Attendance Report'

    @api.model
    def _employees_domain(self):
        domain = [('id', '=', self.env.user.employee_id.id)]
        if self.env.user.has_group('hr_holidays.group_hr_holidays_user'):
            domain = []
        return domain

    @api.model
    def year_selection(self):
        from_date = fields.Date.today() - timedelta(days=5 * 365)
        from_year = from_date.year
        years = []
        to_year = fields.Date().today().year
        to_year = to_year + 1
        while from_year != to_year:
            years.append((str(from_year), str(from_year)))
            from_year += 1
        years.sort(key=lambda year: year[1], reverse=True)
        return years

    year = fields.Selection(year_selection, string="Year", default=str(fields.Date.today().year),
                            required=True)
    month = fields.Selection(MONTHS, string='Months', default=str(fields.Date().today().month),
                             required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', default=lambda self: self.env.user.employee_id,
                                  required=True, domain=_employees_domain)
    employee_number = fields.Char(related='employee_id.employee_number')
    department_id = fields.Many2one('hr.department', related='employee_id.department_id')
    job_id = fields.Many2one('hr.job', related='employee_id.job_id')

    def print_pdf(self):
        data = {
            'form_data': self.read()[0]
        }
        return self.env.ref('plustech_hr_attendance_transaction.report_action_monthly_attendance').report_action(self,
                                                                                                                 data=data)
