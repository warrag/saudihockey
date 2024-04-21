from odoo import fields, models, api


class TravelWay(models.Model):
    _name = 'travel.way'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Travel Way'

    name = fields.Char(translate=True)
    need_ticket = fields.Boolean(string='Need Ticket?')
