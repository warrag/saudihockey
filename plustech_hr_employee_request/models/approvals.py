from odoo import fields, models, api


class BusinessTripApprovals(models.Model):
    _name = 'hr.employee.request.approvals'

    name = fields.Char(string='Title')
    user_id = fields.Many2one('res.users', string='User')
    date = fields.Date(string='Date')
    state = fields.Selection([('approved', 'Approved'), ('reject', 'Rejected')])
    comment = fields.Text(string='Comments')
    employee_request_id = fields.Many2one('hr.employee.request')
