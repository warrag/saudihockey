from odoo import models, fields


class BankAccount(models.Model):
    _inherit = "res.partner.bank"

    cif = fields.Char('CIF')
