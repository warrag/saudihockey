from odoo import fields, models


class EmployeeAllowanceType(models.Model):
    _inherit = 'employee.allowance.type'

    attendance_deduction = fields.Boolean(string='Include In Attendance Deduction',)
