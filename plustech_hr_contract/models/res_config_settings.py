
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    probation_manager_notification = fields.Integer(string='Manager Notification Days', required=True, default=14)
    probation_hr_notification = fields.Integer(string='HR Notification Days', required=True, default=7)
    contract_end_days_hr_reminder = fields.Integer(string='HR Notification Days', required=True, default=7)
    contract_end_days_manager_reminder = fields.Integer(string='Manager Notification Days', required=True, default=7)


class HRConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    probation_manager_notification = fields.Integer(related='company_id.probation_manager_notification',
                                                    required=True, readonly=False)
    probation_hr_notification = fields.Integer(related='company_id.probation_hr_notification', required=True,
                                               readonly=False)
    contract_end_days_hr_reminder = fields.Integer(related='company_id.contract_end_days_hr_reminder', required=True,
                                                   readonly=False)
    contract_end_days_manager_reminder = fields.Integer(related='company_id.contract_end_days_manager_reminder',
                                                        required=True, readonly=False)

