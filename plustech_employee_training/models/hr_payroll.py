# -*- coding: utf-8 -*-

from odoo import models, api, fields


class PayslipTraining(models.Model):
    _inherit = 'hr.payslip'

    courses_ids = fields.Many2many('course.schedule')

    @api.onchange('employee_id', 'date_from', 'date_to')
    def onchange_employee_get_training_inputs(self):
        """
        function used for writing courses record in payslip
        input tree.

        """
        course_type = self.env.ref('plustech_employee_training.hr_payroll_rules_employee_traing_fees')
        contract = self.contract_id
        course_id = self.env['course.schedule'].search([('registered_employees.employee_id', 'in', self.employee_id.ids),
                                                      ('state', '=', 'active'),('payslip_paid', '=', False),('paid_by','=','employee')])
        amount = course_id.mapped('price')
        cash_amount = sum(amount)
        if course_id:
            self.courses_ids = course_id
            input_data = {
                'name': course_type.name,
                'code': course_type.code,
                'amount': cash_amount,
                'contract_id': contract.id,
                'input_type_id': self.env.ref('plustech_employee_training.input_course').id,
            }
            input_lines = self.input_line_ids.browse([])
            input_lines += input_lines.new(input_data)
            self.input_line_ids = input_lines
            

    def action_payslip_done(self):
        """
        function used for marking paid overtime
        request.

        """
        for recd in self.courses_ids:
            recd.payslip_paid = True
        return super(PayslipTraining, self).action_payslip_done()
