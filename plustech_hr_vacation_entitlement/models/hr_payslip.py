# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools import float_round


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    vacation_entitlement_id = fields.Many2one('hr.vacation.entitlement', string='Vacation Entitlement')
    payslip_type = fields.Selection(selection_add=[('leave_salary', 'Leave Salary')])

    def _get_worked_day_lines(self, domain=None, check_out_of_contract=True):
        res = super(HrPayslip, self)._get_worked_day_lines(domain, check_out_of_contract)
        work_entry_type = self.env.ref('plustech_hr_vacation_entitlement.hr_work_entry_type_leave_advance')
        leaves = self.env['hr.vacation.entitlement'].search(
            [('employee_id', '=', self.employee_id.id), ('state', '=', 'validate'),
             ('date_to', '>=', self.date_from), ('date_to', '<=', self.date_to)],
            order="date_to desc", limit=1)
        if leaves:
            self.date_from = leaves.date_to
            number_of_days = (leaves.date_to - leaves.date_from).days
            res.append({
                'sequence': work_entry_type.sequence,
                'work_entry_type_id': work_entry_type.id,
                'number_of_days': number_of_days,
                'is_leave_advance': True,
                'number_of_hours': number_of_days * 8,
            })
        return res


class HrPayslipWorkedDays(models.Model):
    _inherit = 'hr.payslip.worked_days'

    is_leave_advance = fields.Boolean(string='Leave Advance')

    def _compute_amount(self):
        res = super(HrPayslipWorkedDays, self)._compute_amount()
        for line in self:
            if line.is_leave_advance:
                line.amount = - line.amount
        return res

