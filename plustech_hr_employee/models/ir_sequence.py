from odoo import fields, models, api


class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    is_employee_id = fields.Boolean(string='Is Employee ID')
