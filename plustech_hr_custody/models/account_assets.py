from odoo import fields, models, api


class AccountAsset(models.Model):
    _inherit = 'account.asset'

    custody_ok = fields.Boolean(string='Can be custody')
    property_id = fields.Many2one('property.property', domain="[('asset_id', '=', False)]")
    status = fields.Selection([('free', 'Free'), ('allocate', 'Allocated')], string='Status', default='free')
    owner_id = fields.Many2one('hr.employee', string='Owner')
    allocation_date = fields.Date(string='Allocation Date')

    @api.model
    def create(self, values):
        res = super(AccountAsset, self).create(values)
        if values.get('property_id'):
            property_id = self.env['property.property'].browse(int(values.get('property_id')))
            property_id.write({'asset_id': res.id})
        return res

    def write(self, values):
        res = super(AccountAsset, self).write(values)
        if values.get('property_id') and not self.env.context.get('property'):
            property_id = self.env['property.property'].browse(int(values.get('property_id')))
            property_id.write({'asset_id': self.id})
        return res
