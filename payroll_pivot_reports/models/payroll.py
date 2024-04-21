# -*- coding:utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.osv import expression
from ast import literal_eval

class HrPayslipLine(models.Model):
    _inherit = 'hr.payslip.line'

    slip_date_from = fields.Date(related='slip_id.date_from', string='Payslip\'s Date From', store=True)
    slip_date_to = fields.Date(related='slip_id.date_to', string='Payslip\'s Date To', store=True)

    slip_state = fields.Selection(related='slip_id.state', string='Payslip\'s Status', store=True)

    sliprun_id = fields.Many2one(related='slip_id.payslip_run_id', string='Payslip\'s Batch', store=True)

    slip_is_credit_note = fields.Boolean(related='slip_id.credit_note', string='Payslip is a Credit Note', store=True)


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    def batch_report(self):
        self.ensure_one()
        for record in self:
            action, = self.env.ref('payroll_pivot_reports.action_allpaysliplines').read()
            action['domain'] = expression.AND([
                literal_eval(action['domain'] or '[]'),
                [('sliprun_id', '=', record.id)]
            ])
        return action

