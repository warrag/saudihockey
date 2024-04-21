# -*- coding: utf-8 -*-

from datetime import datetime, timedelta, date
from dateutil import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError


class HrLeaveRequest(models.Model):
    _inherit = 'hr.leave'

    flight_ticket = fields.One2many('hr.flight.ticket', 'leave_id', string='Flight Ticket', help="Flight ticket")
    expense_account = fields.Many2one('account.account')
    leave_salary = fields.Selection([('0', 'Basic'), ('1', 'Gross')], string='Leave Salary')
    is_annual_leave = fields.Boolean(related='holiday_status_id.is_annual_leave', string='Is Annual Leave?')
    need_ticket = fields.Boolean(related='holiday_status_id.need_ticket', string='Employee Can Request Ticket?')
    min_days_for_ticket = fields.Integer(related='holiday_status_id.min_days_for_ticket',
                                         string='Minimum Leave Days For Ticket?')

    def book_ticket(self):
        if not self.employee_id.join_date:
            raise ValidationError(_('Please set join date for %s') % self.employee_id.name)
        desver_ticket_after = self.env['ir.config_parameter'].sudo().get_param('desver_ticket_after')
        start_date = self.employee_id.join_date
        end_date = date.today()
        delta = relativedelta.relativedelta(end_date, start_date)
        if delta.months<int(desver_ticket_after):
            raise ValidationError(_('This Employee not deserve leave ticket before %s months from joining date')%int(desver_ticket_after))
        if self.need_ticket and self.holiday_status_id.ticket_except_nationality_ids and \
                self.employee_id.country_id.id in self.holiday_status_id.ticket_except_nationality_ids.ids:
            raise ValidationError(_("You can not request ticket as this employee's nationality not allowed to request ticket"))
        # elif:
        #     raise ValidationError(_('Ticket eligibility has been cancelled'))
        if not self.env.user.has_group('hr_holidays.group_hr_holidays_user'):
            raise UserError(_('Only an HR Officer or Manager can book flight tickets.'))
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_employee_id': self.employee_id.id,
            'default_leave_id': self.id,
            'default_date_start': self.request_date_from,
            'default_date_return': self.request_date_to
        })
        
        return {
            'name': _('Book Flight Ticket'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref('plustech_hr_flight_ticket.view_hr_book_flight_ticket_form').id,
            'res_model': 'hr.flight.ticket',
            'target': 'new',
            'context': ctx,
        }

    def view_flight_ticket(self):
        return {
            'name': _('Flight Ticket'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'hr.flight.ticket',
            'target': 'current',
            'res_id': self.flight_ticket[0].id,
        }

    
