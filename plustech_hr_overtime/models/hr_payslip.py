from odoo import models, api, fields


class PayslipOverTime(models.Model):
    _inherit = 'hr.payslip'

    overtime_ids = fields.Many2many('hr.overtime')

    @api.onchange('employee_id', 'date_from', 'date_to')
    def onchange_employee_get_inputs(self):
        """
        function used for writing overtime record in payslip
        input tree.

        """
        overtime_type = self.env.ref('plustech_hr_overtime.hr_salary_rule_overtime')
        contract = self.contract_id
        overtime_id = self.env['hr.overtime'].search([('employee_id', '=', self.employee_id.id),
                                                      ('contract_id', '=', self.contract_id.id),('overtime_payment', '=', 'payroll'),
                                                      ('state', '=', 'to_pay'), ('payslip_paid', '=', False),
                                                      ('date_from', '>=', self.date_from),
                                                      ('date_to', '<=', self.date_to),
                                                      ])
        hrs_amount = overtime_id.mapped('cash_hrs_amount')
        day_amount = overtime_id.mapped('cash_day_amount')
        cash_amount = sum(hrs_amount) + sum(day_amount)
        attendance_transactions = self.env['attendance.transaction'].search(
            [('employee_id', '=', self.employee_id.id), ('date', '>=', self.att_date_from),
             ('date', '<=', self.att_date_to), ('status', '=', 'ex'),
              ('overtime_amount', '>', 0.0)], order='date ASC')

        auto_computed_overtime = sum(abs(line.overtime_amount) for line in attendance_transactions)
        cash_amount += auto_computed_overtime
        if overtime_id:
            self.overtime_ids = overtime_id
            input_data = {
                'name': overtime_type.name,
                'code': overtime_type.code,
                'amount': cash_amount,
                'contract_id': contract.id,
                'input_type_id': self.env.ref('plustech_hr_overtime.input_overtime').id,
            }
            input_lines = self.input_line_ids.browse([])
            input_lines += input_lines.new(input_data)
            self.input_line_ids = input_lines

    def action_payslip_done(self):
        """
        function used for marking paid overtime
        request.

        """
        for recd in self.overtime_ids:
            if recd.type == 'cash':
                recd.payslip_paid = True
        return super(PayslipOverTime, self).action_payslip_done()
