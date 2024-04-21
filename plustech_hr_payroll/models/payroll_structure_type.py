from odoo import fields, models, api


class HrPayrollStructureType(models.Model):
    _inherit = 'hr.payroll.structure.type'

    company_id = fields.Many2one(
        'res.company', string='Company', copy=False, required=True,
        default=lambda self: self.env.company)
