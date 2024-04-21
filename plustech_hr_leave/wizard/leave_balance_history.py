# -*- coding: utf-8 -*-

from odoo import _, fields, models,api


class LeaveBalanceHistory(models.TransientModel):
    _name = 'leave.balance.history'
    _description = 'Leave Balance History'

    @api.model
    def _employees_domain(self):
        domain = [('id', '=', self.env.user.employee_id.id)]
        if self.env.user.has_group('hr_holidays.group_hr_holidays_user'):
            domain = []
        return domain


    balance_date = fields.Date('Balance at Date',
                               help="Choose a date to get the leave balance at that date",
                               default=fields.Datetime.today(), required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', default=lambda self: self.env.user.employee_id,
                                  required=True, domain=_employees_domain)

    def open_at_date(self):
        tree_view_id = self.env.ref('plustech_hr_leave.views_hr_leave_balance_report').id
        domain = [('employee_id', '=', self.employee_id.id)]
        # We pass `to_date` in the context so that `leave balance` will be computed across
        # balance until date.
        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'), (False, 'form')],
            'view_mode': 'tree',
            'name': _('Leaves Balance'),
            'res_model': 'hr.leave.balance',
            'domain': domain,
            'context': dict(self.env.context, to_date=self.balance_date,
                            create=False, delete=False),
            'display_name': self.balance_date.strftime("%b %d, %Y")
        }
        return action
