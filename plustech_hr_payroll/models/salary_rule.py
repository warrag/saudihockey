from odoo import fields, models


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    company_id = fields.Many2one(
        'res.company', string='Company', copy=False, required=True,
        default=lambda self: self.env.company)
    appears_on_payslip_batch = fields.Boolean(string='Appears on Payslip Batch', default=True)
    background_color = fields.Char(string='Print Background Color')


class HrSalaryRuleCategory(models.Model):
    _inherit = 'hr.salary.rule.category'

    appears_on_payslip_batch = fields.Boolean(string='Appears on Payslip Batch', default=True)
    background_color = fields.Char(string='Print Background Color')
