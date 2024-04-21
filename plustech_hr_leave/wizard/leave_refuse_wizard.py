# -*- coding: utf-8 -*-

from odoo import models, fields
from datetime import date


class LeaveRefuseWizard(models.TransientModel):
    _name = 'leave.refuse.wizard'
    _description = 'Leave  Refuse Wizard'

    reason = fields.Text(string='Reason', required=True)
    send_message = fields.Boolean(string='Send Message')
    leave_id = fields.Many2one('hr.leave')

    def action_reject(self):
        model = self._context.get('active_model')
        record_id = self._context.get('active_id')
        record = self.env[model].browse(record_id)
        if record:
            record.action_refuse()
            record.refuse_reason = self.reason
        return
