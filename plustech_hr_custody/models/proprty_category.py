from odoo import models, fields, api


class PropertyCategory(models.Model):
    _name = 'property.category'

    name = fields.Char(string='Name', translate=True)
