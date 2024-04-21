from odoo import fields, models, api


class HrLoanPolicy(models.Model):
    _name = 'hr.loan.policy'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Hr Loan Policy'
    _check_company_auto = True

    name = fields.Char(string='Policy Name', translate=True, required=True)
    job_position_ids = fields.Many2many('hr.job', string='Job Positions', required=True, check_company=True)
    active = fields.Boolean(string='Active', default=True)
    max_amount = fields.Float(string='Maximum Amount Allowed')
    max_salaries = fields.Float(string='Maximum Salary Allowed')
    salary_type = fields.Selection([('basic', 'Basic Salary'), ('gross', 'Gross Salary')],
                                   string='Salary Type', default='gross')
    max_payment_period = fields.Integer(string='Loan  Term', help='Maximum Payment Period Allowed')
    min_years = fields.Integer(string='Minimum Years Allowed', help='Minimum years between employee last loan')
    allow_multi = fields.Boolean(string='Allow Multiple Loans')
    company_id = fields.Many2one(
        'res.company', string='Company', copy=False, required=True,
        default=lambda self: self.env.company)
