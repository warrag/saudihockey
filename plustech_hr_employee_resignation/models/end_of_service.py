from odoo import fields, models, api


class EndOfService(models.Model):
    _inherit = 'end.of.service.reward'

    resignation_id = fields.Many2one('hr.employee.resignation')
