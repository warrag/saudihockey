# -*- coding: utf-8 -*-

from odoo import models, fields
from datetime import date


class ResignationNoticePeriod(models.TransientModel):
    _name = 'resignation.notice.period'
    _description = 'Resignation Notice Period Wizard'

    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')

    def action_apply(self):
        model = self._context.get('active_model')
        record_id = self._context.get('active_id')
        record = self.env[model].browse(record_id)
        record.write({
            'notice_start': self.start_date,
            'notice_end': self.end_date,
            'state': 'approved'
        })
        return
