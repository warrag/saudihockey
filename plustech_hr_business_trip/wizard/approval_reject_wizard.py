# -*- coding: utf-8 -*-

from odoo import models, fields
from datetime import date


class ApprovalRejectWizard(models.TransientModel):
    _name = 'approval.reject.wizard'
    _description = 'Approval  Reject Wizard'

    reason = fields.Text(string='Rejection Reason', required=True)

    def action_reject(self):
        model = self._context.get('active_model')
        record_id = self._context.get('active_id')
        record = self.env[model].browse(record_id)
        record.write({
            'approval_ids': [(0, 0, {'user_id': self.env.user.id, 
                                     'name': record.state,
                                     'key': record.state,
                                     'comment': self.reason, 
                                     'state': 'reject', 
                                     'date': date.today()})],
            'state': 'reject'
        })
        return
