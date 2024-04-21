from odoo import fields, models, api


class BusinessTripApprovals(models.Model):
    _name = 'hr.request.approvals.flight.ticket'

    name = fields.Char(string='Title')
    key = fields.Char(string='key')
    user_id = fields.Many2one('res.users', string='User')
    date = fields.Date(string='Date')
    state = fields.Selection([('approved', 'Approved'), ('reject', 'Rejected')])
    comment = fields.Text(string='Comments')
    ticket_id = fields.Many2one('hr.flight.ticket')
