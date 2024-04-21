from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    include_family = fields.Boolean(string='Family Include')
    medical_insurance_product_id = fields.Many2one('product.product', domain=[('detailed_type', '=', 'service')])


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    include_family = fields.Boolean(string='Family Include', related="company_id.include_family", readonly=False)
    medical_insurance_product_id = fields.Many2one('product.product', string='Family Include',
                                                   related="company_id.medical_insurance_product_id",
                                                   readonly=False, domain=[('detailed_type', '=', 'service')])

