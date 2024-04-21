from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    create_appraisal = fields.Selection(string='Auto Create Appraisal?', selection=[
        ('manually', 'Manually'),
        ('automatically', 'Automatically'),
    ], required=True, deafult='manually', config_parameter='plustech_hr_appraisal.create_appraisal',)

    appraisal_type = fields.Selection(string='Type', selection=[
        ('1', 'Monthly'),
        ('3', 'quarterly'),
        ('6', 'Semi'),
        ('12', 'Annually'),
    ], default='12', required=True, config_parameter='plustech_hr_appraisal.appraisal_type', )