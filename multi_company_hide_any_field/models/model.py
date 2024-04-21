from odoo import api, fields, models, _


class ResCompany(models.Model):
    _inherit = 'res.company'


    field_configuration_ids = fields.One2many('field.configuration', 'company_id', string='Field Configuration')


class FieldConfiguration(models.Model):
    _name = 'field.configuration'
    _description = 'Field Configuration'


    model_id = fields.Many2one('ir.model', string='Model', required=True,index=True, ondelete='cascade')
    field_id = fields.Many2one('ir.model.fields', string='Field', required=True, ondelete='cascade',
        domain="[('model_id', '=', model_id)]")
    field_name = fields.Char(related='field_id.name', string='Technical Name', readonly=True)
    readonly = fields.Boolean('ReadOnly', default=False)
    invisible = fields.Boolean('Invisible', default=False)
    user_ids = fields.Many2many('res.users', 'hide_field_user_rel', 'field_line_id', 'user_id', string='User',
                                required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True)

    _sql_constraints = [
        ('field_model_readonly_unique', 'UNIQUE ( field_id, model_id, readonly)',
         _('Readonly Attribute Is Already Added To This Field, You Can Add Group To This Field!')),
        ('model_field_invisible_uniq', 'UNIQUE (model_id, field_id, invisible)',
         _('Invisible Attribute Is Already Added To This Field, You Can Add Group To This Field'))
    ]

    @api.onchange('model_id')
    def _onchange_model_id(self):
        domain = {'domain':{'field_id':[('model_id','=',self.model_id.id)]}}
        return domain
