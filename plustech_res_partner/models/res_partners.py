from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    short_address = fields.Char("Short Address")
    building = fields.Char("Building")
    company_registry = fields.Char("Company Registry")
    secondary = fields.Char("Secondary")
    district = fields.Char("District")

    def name_get(self):
        res = super(ResPartner, self).name_get()
        new_res = []
        for partner in res:
            full_string = partner[1].split("\n")
            partner_ref = self.browse(partner[0]).ref
            full_string[0] += " [" + partner_ref + "]" if partner_ref else ""
            new_res.append((partner[0], "\n".join(full_string)))
        return new_res

    @api.depends('is_company', 'name', 'parent_id.display_name', 'type', 'company_name', 'ref')
    def _compute_display_name(self):
        return super(ResPartner, self)._compute_display_name()

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        args = list(args or [])
        if name:
            args += ['|', '|', '|', '|', ('name', operator, name), ('ref', operator, name),
                     ('email', operator, name),
                     ('company_registry', operator, name),
                     ('mobile', operator, name)]
        return self._search(args, limit=limit, access_rights_uid=name_get_uid)
