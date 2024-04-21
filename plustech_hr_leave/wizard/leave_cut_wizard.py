# -*- coding: utf-8 -*-

from odoo import models, fields,_
from datetime import timedelta
from pytz import timezone
import pytz


class LeaveCutWizard(models.TransientModel):
    _name = 'leave.cut.wizard'
    _description = 'Leave  Cut Wizard'

    reason = fields.Text(string='Reason', required=True)
    leave_id = fields.Many2one('hr.leave')
    cut_date = fields.Date(string='Return  Date', default=fields.Date.context_today, )

    def action_apply(self):
        model = self._context.get('active_model')
        record_id = self._context.get('active_id')
        holiday = self.env[model].browse(record_id)
        if holiday:
            date_from = holiday.request_date_from
            date_to = holiday.request_date_to
            cut_date = self.cut_date - timedelta(days=1)
            holiday.with_context(leave_skip_state_check=True).write({'request_date_to': cut_date,
                          'cut_done': True})
            holiday.message_post(
                body=_(
                    'Your %(leave_type)s planned form %(start_date)s to %(date_to)s has been cut.\n Your return date is'
                    '%(end_date)s\n Leave Cut reason: \n %(reason)s',
                    leave_type=holiday.holiday_status_id.display_name,
                    start_date=date_from,
                    date_to=date_to,
                    end_date=self.cut_date,
                    reason=self.reason
                ),
                partner_ids=holiday.employee_id.user_id.partner_id.ids)
        return
