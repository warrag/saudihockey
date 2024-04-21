from odoo import models, fields


class ResourceResource(models.Model):
    _inherit = "resource.resource"

    name = fields.Char(translate=True)
