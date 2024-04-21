from datetime import datetime
import string
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class BusinessTripActivity(models.Model):
    _name = 'business.trip.activity'


    type = fields.Selection([
        ('trip', 'Business Trip'),
        ('ticket', 'Business Trip Ticket')
    ], string='Type')
    activity_type_id = fields.Many2one('mail.activity.type', string='Activity Type', required=True)
    users_id = fields.Many2one('res.users', string='Users')
    note = fields.Char('Note', required=True)
    subject = fields.Char('Subject')
    business_trip_ticket_state = fields.Selection([('report', 'Waiting For Administrative Affairs Report'),
                                                   ('admin', 'Waiting For the Director of Financial and Administrative Affairs Approval'),
                                                   ('ceo', 'Waiting for CEO Approval'), 
                                                   ('booked','Booked')], string='State')
    
    business_trip_state = fields.Selection([('new', 'New'), 
                                            ('direct_manager', 'Waiting Manager Approval'),
                                            ('acceptance', 'Employee Acceptance'), 
                                            ('hr', 'Waiting HR Officer Approval'),
                                            ('hrm', 'Waiting HRM Approval'),
                                            ('finance', 'Waiting For  Director of Financial and Administrative Affairs Approval'),
                                            ('ceo', 'Waiting CEO Approval'),
                                            ('to_pay', 'To Pay')], string='State')


    