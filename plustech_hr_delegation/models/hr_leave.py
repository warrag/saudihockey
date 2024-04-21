# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
from odoo.addons.hr_holidays.models.hr_leave import HolidaysRequest
from collections import defaultdict
from pytz import timezone, UTC


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    delegated_employee_id = fields.Many2one('hr.employee', string='Delegated Employee')
    need_delegation = fields.Boolean(related='holiday_status_id.need_delegation', string='Need delegation')

    def action_validate(self):
        res = super(HrLeave, self).action_validate()
        for record in self:
            if record.need_delegation and record.delegated_employee_id:
                values = {
                    'employee_id': record.employee_id.id,
                    'delegated_employee_id': record.delegated_employee_id.id or False,
                    'from_date': record.request_date_from,
                    'to_date': record.request_date_to,
                    'description': record.name or '%s delegation' % record.holiday_status_id.name
                }
                delegation = self.env['hr.employee.delegation'].sudo().create(values)
                if delegation:
                    delegation.action_submit()
        return res
