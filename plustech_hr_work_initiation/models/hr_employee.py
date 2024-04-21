from odoo import fields, models, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    last_annual_leave_status = fields.Selection([
        ('none', 'No Leave'),
        ('return', 'return'),
        ('not_return', 'Not Return')
    ], default='none', string='Last Annual Leave Status')
    last_annual_leave_id = fields.Many2one('hr.leave', string='Last Annual Leave')
    last_annual_return_date = fields.Date(string='Last Annual Leave Return Date')

    def _compute_last_annual_leave(self):
        holidays = self.env['hr.leave'].sudo().search([
            ('employee_id', 'in', self.ids),
            ('is_annual_leave', '=', True),
            ('state', 'not in', ('cancel', 'refuse'))
        ])
        for holiday in holidays:
            employee = self.filtered(lambda e: e.id == holiday.employee_id.id)
            employee.last_annual_leave_id = holiday.id
        if self.last_annual_leave_id and not self.last_annual_return_date:
            self.last_annual_leave_status = 'not_return'
            allocations = self.env['hr.leave.allocation'].sudo().search([
                ('employee_id', 'in', self.ids),
                ('allocation_type.is_annual_leave', '=', True),
                ('state', 'not in', ('cancel', 'refuse', 'draft'),
                 '|', ('date_to', '=', False), ('date_to', '>', fields.Date.today())
                 )
            ])
            for allocation in allocations:
                allocation.nextcall = False


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    last_annual_leave_status = fields.Selection([
        ('none', 'No Leave'),
        ('return', 'return'),
        ('not_return', 'Not Return')
    ], default='none', string='Last Annual Leave Status')
    last_annual_leave_id = fields.Many2one('hr.leave', string='Last Annual Leave')
    last_annual_return_date = fields.Date(string='Last Annual Leave Return Date')
