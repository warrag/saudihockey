from odoo import fields, models, api


class LoanType(models.Model):
    _name = 'loan.type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Loan Type'
    _check_company_auto = True

    name = fields.Char(string='Loan type', translate=True)
    loan_policy_id = fields.Many2one('hr.loan.policy', string='Loan Policy', required=True,
                                     check_company=True)
    acknowledgment = fields.Text(string='Acknowledgment', required=True)
    company_id = fields.Many2one(
        'res.company', string='Company', copy=False, required=True,
        default=lambda self: self.env.company)

