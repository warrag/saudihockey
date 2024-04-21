from datetime import datetime
import string
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class FlightActivity(models.Model):
    _name = 'flight.activity'


    type = fields.Selection([
        ('trip', 'Business Trip Ticket'),
        ('leave', 'Leave Ticket')
    ], string='Type')
    activity_type_id = fields.Many2one('mail.activity.type', string='Activity Type', required=True)
    users_id = fields.Many2one('res.users', string='Users', required=True)
    note = fields.Char('Note', required=True)
    subject = fields.Char('Subject')
    ticket_state = fields.Selection([('report', 'Waiting For Administrative Affairs Report'),
                                                   ('admin', 'Waiting For the Director of Financial and Administrative Affairs Approval'),
                                                   ('ceo', 'Waiting for CEO Approval'), 
                                                   ('booked','Booked')], string='State')


    