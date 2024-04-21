# -*- coding: utf-8 -*-

from datetime import datetime
import string
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class HrFlightTicket(models.Model):
    _name = 'hr.flight.ticket'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char()
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, help="Employee")
    ticket_type = fields.Selection([('one', 'One Way'), ('round', 'Round Trip')], string='Ticket Type', default='round',
                                   help="Select the ticket type")
    depart_from = fields.Char(string='Departure', required=False, help="Departure")
    destination = fields.Char(string='Destination', required=False, help="Destination")
    date_start = fields.Date(string='Start Date', required=True, help="Start date")
    date_return = fields.Date(string='Return Date', help="Return date")
    ticket_class = fields.Selection([('economy', 'Economy'),
                                     ('premium_economy', 'Premium Economy'),
                                     ('business', 'Business'),
                                     ('first_class', 'First Class')], string='Class', help="Select the ticket class")
    ticket_fare = fields.Float(string='Ticket Fare', help="Give the ticket fare")
    flight_details = fields.Text(string='Flight Details', help="Flight details")
    return_flight_details = fields.Text(string='Return Flight Details', help="return flight details")
    state = fields.Selection([('booked', 'Draft'), ('confirmed', 'Director of Financial and Administrative Affairs Approval'),
                             ('paid', 'paid'), ('canceled', 'Canceled')],
                             string='Status', default='booked')
    invoice_id = fields.Many2one('account.move', string='Invoice', help="Invoice")
    leave_id = fields.Many2one('hr.leave', string='Leave', help="Leave")
    company_id = fields.Many2one('res.company', 'Company', help="Company",
                                 default=lambda self: self.env.user.company_id)
    air_line_id = fields.Many2one('res.partner', string='Air Line')
    trip_id = fields.Many2one('flight.ticket.allowance', 'Trip')
    adults = fields.Integer(string='Adults', default=1)
    chailds = fields.Integer(string='Chailds')
    infants = fields.Integer(string='Infants')
    payslip_paid = fields.Boolean('Paid in Payslip', readonly=True)
    paid_for_employee = fields.Boolean('Paid For employee', help="Paid ticket cost for employee as allowance!")
    dependent_ids = fields.Many2many('hr.employee.family', string='Dependents', help='Employee dependents')
    ticket_no = fields.Char(string='Ticket No.')

    def name_get(self):
        res = []
        for ticket in self:
            res.append((ticket.id, _("Flight ticket: %s on %s to %s") % (
                ticket.leave_id.holiday_status_id.name, ticket.date_start.strftime("%m/%d/%Y"),
                ticket.trip_id.destination_city_id.name)))
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

    def confirm_ticket(self):
        # if not self.paid_for_employee:
        #     product_id = self.env['product.product'].search([("name", "=", "Flight Ticket")])
        #     if self.ticket_fare <= 0:
        #         raise UserError(_('Please add ticket fare.'))
        #     inv_obj = self.env['account.move']
        #     expense_account = self.env['ir.config_parameter'].sudo().get_param('travel_expense_account')
        #     if not expense_account:
        #         raise UserError(_('Please select expense account for the flight tickets.'))
        #     tickets_analytic_account_id = self.env['ir.config_parameter'].sudo().get_param(
        #         'tickets_analytic_account_id')
        #     domain = [
        #         ('type', '=', 'purchase'),
        #         ('company_id', '=', self.company_id.id),
        #     ]
        #     journal_id = self.env['account.journal'].search(domain, limit=1)
        #     partner = self.air_line_id
        #     if not partner.property_payment_term_id:
        #         date_due = fields.Date.context_today(self)
        #     else:
        #         pterm = partner.property_payment_term_id
        #         pterm_list = \
        #             pterm.with_context(currency_id=self.env.user.company_id.id).compute(
        #                 value=1, date_ref=fields.Date.context_today(self))[0]
        #         date_due = max(line[0] for line in pterm_list)
        #     inv_id = inv_obj.create({
        #         'name': '/',
        #         'invoice_origin': 'Flight Ticket',
        #         'move_type': 'in_invoice',
        #         'journal_id': journal_id.id,
        #         # 'invoice_payment_term_id': partner.property_payment_term_id.id,
        #         'invoice_date_due': date_due,
        #         'ref': False,
        #         'partner_id': partner.id,
        #         # 'invoice_partner_bank_id': partner.property_account_payable_id.id,
        #         'state': 'draft',
        #         'invoice_line_ids': [(0, 0, {
        #             'name': 'Flight Ticket',
        #             'price_unit': self.ticket_fare,
        #             'quantity': 1.0,
        #             'account_id': int(expense_account),
        #             'product_id': product_id.id,
        #             'analytic_account_id': int(tickets_analytic_account_id),
        #         })],
        #     })
        #     # inv_id.action_invoice_open()
        #     self.write({'state': 'confirmed', 'invoice_id': inv_id.id})
        # else:
        self.write({'state': 'confirmed'})

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

    # @api.model
    # def run_update_ticket_status(self):
    #     run_out_tickets = self.search([('state', 'in', ['confirmed', 'started']),
    #                                    ('date_return', '<=', datetime.now())])
    #     confirmed_tickets = self.search([('state', '=', 'confirmed'), ('date_start', '<=', datetime.now()),
    #                                      ('date_return', '>', datetime.now())])
    #     for ticket in run_out_tickets:
    #         ticket.write({'state': 'completed'})
    #     for ticket in confirmed_tickets:
    #         ticket.write({'state': 'started'})

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
