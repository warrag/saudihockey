from odoo import fields, models


class ModelName(models.Model):
    _name = 'duty.commencement.type'
    _description = 'Duty Commencement Type'
    _order = 'sequence'

    sequence = fields.Integer("Sequence", default=10)
    name = fields.Char(string='Name', translate=True, required=True)
