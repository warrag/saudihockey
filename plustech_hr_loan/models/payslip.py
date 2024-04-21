from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import random
import time
from datetime import datetime, date, time, timedelta
import dateutil.parser
import pytz
from pytz import timezone, UTC


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    loan_ids = fields.One2many('hr.loan.line', 'payslip_id', string="Loans")
    total_paid = fields.Float(string="Total Loan Amount", compute='compute_total_paid')

    @api.depends('loan_ids')
    def compute_total_paid(self):
        """This compute the total paid amount of Loan.
            """
        total = 0.0
        for slip in self:
            for line in slip.loan_ids:
                if line.paid:
                    total += line.amount
            slip.total_paid = total
            total = 0.0

    def get_loan(self):
        """This gives the installment lines of an employee where the state is not in paid.
            """
        # print("...............    ", self.employee_id)
        loan_ids = self.env['hr.loan.line'].search([('employee_id', '=', self.employee_id.id),
                                                    ('date', '>=', self.date_from), ('date', '<=', self.date_to),
                                                    ('paid', '=', False)])

        for loan in loan_ids:
            if loan.loan_id.state == 'approve':
                loan.write({'payslip_id': self.ids[0]})
        return True

    def action_payslip_cancel(self):
        for line in self.loan_ids:
            line.paid = False
        res = super(HrPayslip, self).action_payslip_cancel()
        return res
