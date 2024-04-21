from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'
    is_trainer = fields.Boolean('Is a Trainer')