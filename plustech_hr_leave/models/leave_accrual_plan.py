from odoo import fields, models, api


class LeaveAccrualPlan(models.Model):
    _inherit = 'hr.leave.accrual.plan'

    cumulative_balance = fields.Boolean(string='Cumulative Balance',
                                        help='count cumulative balance from employee join date')
