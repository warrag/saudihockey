# -*- coding: utf-8 -*-

from datetime import datetime, date
import string
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


STATUS = {'draft': 'Draft',
          'report': 'Administrative Affairs Report Approval',
          'booked': 'Booked',
          'admin': 'Director of Financial and Administrative Affairs Approval',
          'ceo': 'CEO Approval',
          'canceled': 'Canceled',
        }



class HrFlightTicket(models.Model):
    _name = 'hr.flight.ticket'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char()
    type = fields.Selection([
        ('leave', 'Leave'),
        ('business_trip', 'Business Trip'),
    ], string='Type')

    # employee info
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, help="Employee")
    department_id = fields.Many2one(related="employee_id.department_id", string='Department')
    job_title = fields.Char(related="employee_id.job_title", string='Job Title')
    employee_no = fields.Char(related="employee_id.employee_number", string='Employee Number')

    # flight info
    air_line_id = fields.Many2one('res.partner', string='Air Line', domain="[('is_airline','=',True)]")
    flight_class_id = fields.Many2one('flight.class', string='Flight Class')
    ticket_no = fields.Char(string='Ticket No.')
    ticket_fare = fields.Float(string='Ticket Fare', help="Give the ticket fare")
    ticket_type = fields.Selection([('one', 'One Way'), ('round', 'Round Trip')], string='Ticket Type', default='round', help="Select the ticket type")
    date_start = fields.Date(string='Start Date', required=True, help="Start date")
    date_return = fields.Date(string='Return Date', help="Return date")
    note = fields.Text(string='Notes')

    # flight route
    country_from_id = fields.Many2one('res.country', string='Country')
    city_from_id = fields.Many2one('res.city', string='City')
    country_to_id = fields.Many2one('res.country', string='Country')
    city_to_id = fields.Many2one('res.city', string='City')

    # flight details
    flight_details = fields.Text(string='Flight Details', help="Flight details")
    return_flight_details = fields.Text(string='Return Flight Details', help="return flight details")

    # other info
    leave_id = fields.Many2one('hr.leave', string='Leave', help="Leave")
    company_id = fields.Many2one('res.company', 'Company', help="Company", default=lambda self: self.env.user.company_id)
    payslip_paid = fields.Boolean('Paid in Payslip', readonly=True)
    paid_for_employee = fields.Boolean('Paid For employee', help="Paid ticket cost for employee as allowance!")

    
    state = fields.Selection([('draft', 'Draft'), 
                              ('report', 'Waiting For Administrative Affairs Report'),
                              ('admin', 'Waiting For the Director of Financial and Administrative Affairs Approval'),
                              ('ceo', 'Waiting for CEO Approval'), 
                              ('booked','Booked'), 
                              ('canceled', 'Canceled')], string='Status', default='draft', tracking=True)
    

    invoice_id = fields.Many2one('account.move', string='Invoice', help="Invoice")
    depart_from = fields.Char(string='Departure', required=False, help="Departure")
    destination = fields.Char(string='Destination', required=False, help="Destination")
    trip_id = fields.Many2one('flight.ticket.allowance', 'Trip')
    adults = fields.Integer(string='Adults', default=1)
    chailds = fields.Integer(string='Chailds')
    infants = fields.Integer(string='Infants')

    approval_ids = fields.One2many('hr.request.approvals.flight.ticket', 'ticket_id', string="Approver's")

    
    dependent_ids = fields.Many2many('hr.employee.family', string='Dependents', help='Employee dependents')


    def name_get(self):
        res = []
        for ticket in self:
            if ticket.type == 'leave':
                res.append((ticket.id, _("Flight ticket: %s on %s to %s") % (
                    ticket.leave_id.holiday_status_id.name, ticket.date_start.strftime("%m/%d/%Y"),
                    ticket.trip_id.destination_city_id.name)))
            else:
                res.append((ticket.id, _("Flight ticket: %s on %s") % (ticket.deputation_id.name or '', ticket.date_start.strftime("%m/%d/%Y"))))
        return res

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        self.dependent_ids = False
        dependents = self.env['hr.employee.family'].search([('employee_id', '=', self.employee_id.id)])
        self.dependent_ids = dependents

    @api.onchange('dependent_ids')
    def _onchange_dependent_ids(self):
        adults = len(self.dependent_ids.filtered(lambda line: line.age > 11))
        self.adults = adults+1
        self.chailds = len(self.dependent_ids.filtered(lambda line: 2 <= line.age < 12))
        self.infants = len(self.dependent_ids.filtered(lambda line: line.age < 2))

    @api.onchange('trip_id', 'adults', 'chailds', 'infants')
    def _onchange_trip_id(self):
        trip = self.trip_id
        self.ticket_fare = (trip.adult_fare * self.adults) + (trip.chaild_fare * self.chailds) + (
                    trip.infant_fare * self.infants)

    @api.constrains('date_start', 'date_return')
    def check_valid_date(self):
        if self.filtered(lambda c: c.date_return and c.date_start > c.date_return):
            raise ValidationError(_('Flight travelling start date must be less than flight return date.'))

    def book_ticket(self):
        return {'type': 'ir.actions.act_window_close'}

    def action_generate_payment(self):
        result = self.env.ref('account.action_account_payments').read()[0]
        view_id = self.env.ref('account.view_account_payment_form').id
        result.update({'views': [(view_id, 'form')], })
        result['context'] = {
            'default_partner_id': self.employee_id.address_home_id.id,
            'default_payment_type': 'outbound',
            'default_partner_type': 'supplier',
            'default_amount': self.ticket_fare,
            'default_vacation_ticket_id': self.id
        }
        return result

    def action_payment_view(self):
        self.ensure_one()
        action, = self.env.ref('account.action_account_payments_payable').read()
        action['domain'] = [('vacation_ticket_id', '=', self.id)]
        return action

    def cancel_ticket(self):
        if self.state == 'booked':
            self.write({'state': 'canceled'})
        elif self.state == 'confirmed':
            if self.invoice_id and self.invoice_id.state == 'draft':
                self.write({'state': 'canceled'})
            if self.invoice_id and self.invoice_id.state == 'open':
                self.invoice_id.action_invoice_cancel()
                self.write({'state': 'canceled'})

    

    def action_view_invoice(self):
        return {
            'name': _('Flight Ticket Invoice'),
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_move_form').id,
            'res_model': 'account.move',
            'context': "{'type':'in_invoice'}",
            'type': 'ir.actions.act_window',
            'res_id': self.invoice_id.id,
        }

    def print_ticket(self):
        return self.env.ref("plustech_hr_flight_ticket.business_trip_ticket_report_action").report_action(self)

    def action_submit(self):
        ticket_activity = self.env['flight.activity'].sudo().search([('type', '=', 'trip'), ('ticket_state', '=', 'report')])
        for activity in ticket_activity:
            self.create_activity(activity)
        self.write({'state': 'report'})

    def action_report(self):
        previous_ticket_activity = self.env['flight.activity'].sudo().search([('type', '=', 'trip'), ('ticket_state', '=', 'report')])
        for activity in previous_ticket_activity:
            self._action_feedback_activity(self.env.user, activity.activity_type_id)
        
        self.sudo().write({
                'approval_ids': [(0, 0, {'user_id': self.env.user.id, 
                                         'name': STATUS[self.state],
                                         'state': 'approved', 
                                         'key': self.state, 
                                         'date': date.today()})],
            })
        self.write({'state': 'admin'})
        ticket_activity = self.env['flight.activity'].sudo().search([('type', '=', 'trip'), ('ticket_state', '=', 'admin')])
        for activity in ticket_activity:
            self.create_activity(activity)

    def action_admin_approve(self):
        previous_ticket_activity = self.env['flight.activity'].sudo().search([('type', '=', 'trip'), ('ticket_state', '=', 'admin')])
        for activity in previous_ticket_activity:
            self._action_feedback_activity(self.env.user, activity.activity_type_id)
        self.sudo().write({
                'approval_ids': [(0, 0, {'user_id': self.env.user.id, 
                                         'name': STATUS[self.state],
                                         'state': 'approved', 
                                         'key': self.state, 
                                         'date': date.today()})],
            })
        self.write({'state': 'ceo'})
        ticket_activity = self.env['flight.activity'].sudo().search([('type', '=', 'trip'), ('ticket_state', '=', 'ceo')])
        for activity in ticket_activity:
            self.create_activity(activity)

    def confirm_ticket(self):
        previous_ticket_activity = self.env['flight.activity'].sudo().search([('type', '=', 'trip'), ('ticket_state', '=', 'ceo')])
        for activity in previous_ticket_activity:
            self._action_feedback_activity(self.env.user, activity.activity_type_id)
        self.sudo().write({
                'approval_ids': [(0, 0, {'user_id': self.env.user.id, 
                                         'name': STATUS[self.state],
                                         'state': 'approved', 
                                         'key': self.state, 
                                         'date': date.today()})],
            })
        self.write({'state': 'booked'})
        ticket_activity = self.env['flight.activity'].sudo().search([('type', '=', 'trip'), ('ticket_state', '=', 'booked')])
        for activity in ticket_activity:
            self.create_activity(activity)

    def create_activity(self, activity, user=False,):
        if activity:
            for obj in activity:
                self.env['mail.activity'].sudo().create({
                    'activity_type_id': obj.activity_type_id.id,
                    'res_id': self.id,
                    'res_model_id': self.env['ir.model'].sudo().search([('model', '=', 'hr.flight.ticket')], limit=1).id,
                    'icon': 'fa-pencil-square-o',
                    'date_deadline': fields.Date.today(),
                    'user_id': obj.users_id.id,
                    'summary': obj.subject if obj.subject else False,
                    'note': obj.note,
                })

    def _action_feedback_activity(self, user, activity_type):
        for record in self:
            self.sudo()._get_user_approval_activities(user=user,
                                                      activity_type=activity_type,
                                                      record=record).action_feedback()
    
    def _get_user_approval_activities(self, user=False, activity_type=False, record=False):
        domain = [
            ('res_model', '=', 'hr.flight.ticket'),
            ('res_id', 'in', record.ids),
            ('activity_type_id', '=', activity_type.id)]
        activities = self.env['mail.activity'].search(domain)
        return activities

class FlightTicketAllowance(models.Model):
    _name = 'flight.ticket.allowance'

    departure_city_id = fields.Many2one('res.country.state', string='Departure')
    destination_city_id = fields.Many2one('res.country.state', string='Destination')
    adult_fare = fields.Float(string='Adult Fare')
    chaild_fare = fields.Float(string='Chaild Fare')
    infant_fare = fields.Float(string='Infant Fare')

    def name_get(self):
        res = []
        for record in self:
            name = "/"
            if record.departure_city_id and record.destination_city_id:
                departure = record.departure_city_id
                destination = record.destination_city_id
                name = departure.name + "(" + departure.country_id.name + ")" + " - " + destination.name + "(" + destination.country_id.name + ")"
            res.append((record.id, name))
        return res
