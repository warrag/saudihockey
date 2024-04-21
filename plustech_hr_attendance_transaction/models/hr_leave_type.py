from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    is_permission = fields.Boolean(string='Is Permission?')
        
