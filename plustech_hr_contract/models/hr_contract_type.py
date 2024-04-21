from odoo import fields, models


class HrContractType(models.Model):
    _name = 'hr.contract.type'
    _inherit = ['hr.contract.type', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(translate=True, required=True)
    end_of_service = fields.Boolean(string='Has end of service?')
    has_vacations = fields.Boolean(string='Has vacations?')
    has_medical_insurance = fields.Boolean(string='Has medical insurance?')
    has_allowance = fields.Boolean(string='Has allowance?')
    duration_type = fields.Selection([('limited', 'Limited'), ('unlimited', 'Unlimited')],
                                     string='Duration Type', default='limited')

