from odoo import fields, models, api


class WorkInitiationApprovals(models.Model):
    _name = 'hr.work.initiation.approvals'

    name = fields.Char(string='Title')
    user_id = fields.Many2one('res.users', string='User')
    date = fields.Date(string='Date')
    state = fields.Selection([('approved', 'Approved'), ('reject', 'Rejected')])
    comment = fields.Text(string='Comments')
    request_id = fields.Many2one('hr.work.initiation')
