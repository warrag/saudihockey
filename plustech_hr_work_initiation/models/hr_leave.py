from odoo import fields, models, api


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    def action_approve(self):
        res = super(HrLeave, self).action_approve()
        allocations = self.env['hr.leave.allocation'].sudo().search([
            ('employee_id', 'in', self.ids),
            ('holiday_status_id.is_annual_leave', '=', True),
            ('state', 'not in', ['cancel', 'refuse', 'draft']), 
            '|', ('date_to', '=', False), ('date_to', '>', self.date_from)
        ])
        for allocation in allocations:
            allocation.nextcall = False
        return res
