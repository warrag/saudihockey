from odoo import fields, models, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    expense_ok = fields.Boolean('Can Be Expense')
