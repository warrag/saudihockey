from odoo import fields, models, api,_
from odoo.exceptions import ValidationError


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    attendance_ded = fields.Float(string='Attendance Month Deduction', compute='compute_attendance_ded')
    attendance_sheet_id = fields.Many2one('hr.attendance.sheet', string='Attendance Sheet')

    @api.depends('employee_id', 'date_from', 'date_to', 'attendance_sheet_id')
    def compute_attendance_ded(self):
        for record in self:
            total_ded = 0.0
            record.attendance_sheet_id = self.env['hr.attendance.sheet'].search([('state', '=', 'approve'),
                                                                                 ('date_from', '>=', record.date_from),
                                                                                 ('date_to', '<=', record.date_to)
                                                                                 ], limit=1)

            if record.attendance_sheet_id:
                for ded in record.attendance_sheet_id.line_ids.filtered(
                        lambda line: line.employee_id == record.employee_id):
                    total_ded += ded.total_ded_amount
            record.attendance_ded = total_ded

    def compute_sheet(self):
        for record in self:
            if record.payslip_type == 'normal':
                current_month_attendance = self.env['hr.attendance.sheet'].search([('state', '=', 'approve'),
                                                                                   ('date_from', '>=', record.date_from),
                                                                                   ('date_to', '<=', record.date_to)
                                                                                   ])
                record.attendance_sheet_id = current_month_attendance[0] if len(current_month_attendance) > 0 else False
                if not current_month_attendance:
                    raise ValidationError(_("Attendance sheet for %s has not been approved") %(record.date_from).strftime('%B %Y'))

        return super(HrPayslip, self).compute_sheet()
