from odoo import models, fields, api
from datetime import timedelta


class MonthlyAttendanceReport(models.AbstractModel):
    _name = 'report.plustech_hr_attendance_transaction.monthly_report'

    @api.model
    def _get_report_values(self, docids, data=None):
        today_date = fields.Date().today()
        year = data['form_data'].get('year')
        month = data['form_data'].get('month')
        date_from = today_date.replace(year=int(year), month=int(month), day=1)
        date_to = (date_from.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        employee_id = data['form_data'].get('employee_id')
        domain = [('employee_id', '=', employee_id[0]), ('date', '>=', date_from), ('date', '<=', date_to)]

        transactions = self.env['attendance.transaction'].search(domain, order='date asc')
        return {
            'doc_ids': docids,
            'doc_model': 'attendance.transaction',
            'docs': transactions,
            'data': data,
        }
