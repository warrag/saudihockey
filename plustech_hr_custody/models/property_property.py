from odoo import models, fields, api


class PropertyProperty(models.Model):
    _name = 'property.property'

    name = fields.Char(string="Name", translate=True)
    asset_id = fields.Many2one('account.asset', string='Related Asset',
                               domain=[('linked_product_id', '=', False),
                                       ('asset_type', '=', 'purchase'), ('state', '!=', 'model')])
    status = fields.Selection([('free', 'Free'), ('allocate', 'Allocated')], string='Status', default='free')
    description = fields.Text(string="Description")
    ref = fields.Char(string="Internal Reference")
    categ_id = fields.Many2one('property.category', string="Category", required=True)
    image_1920 = fields.Image("Image")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    @api.model
    def create(self, values):
        res = super(PropertyProperty, self).create(values)
        if values.get('asset_id'):
            asset = self.env['account.asset'].browse(int(values.get('asset_id')))
            asset.write({'property_id': res.id,
                         'custody_ok': True})
        return res

    def write(self, values):
        res = super(PropertyProperty, self).write(values)
        if values.get('asset_id'):
            asset = self.env['account.asset'].browse(int(values.get('asset_id')))
            asset.with_context(property=True).write({'property_id': self.id,
                                                    'custody_ok': True})
        return res
