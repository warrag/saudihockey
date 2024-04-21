from odoo import fields, models, api


class HrPayrollApprovalStatus(models.Model):
    _name = 'hr.payroll.approval.status'
    _description = 'Payroll Approval Status'

    action = fields.Char(string='Action')
    user_id = fields.Many2one('res.users', string='User')
    action_date = fields.Date(string='Action Date')
    batch_id = fields.Many2one('hr.payslip.run', string='Batch')
    stage_id = fields.Many2one('payslip.run.stage', string='Status')
