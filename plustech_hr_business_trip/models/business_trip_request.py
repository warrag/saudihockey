# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, date, timedelta

from odoo.addons.plustech_hr_employee.models.tools import convert_gregorian_to_hijri


class BusinessTripRequest(models.Model):
    _name = 'hr.deputation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Business Trip Request'
    _order = 'id desc'

    @api.model
    def _default_journal_id(self):
        """ The journal is determining the company of the accounting entries generated from business trip. We need to
        force journal company and business trip  company to be the same. """
        default_company_id = self.default_get(['company_id'])['company_id']
        journal = self.env['account.journal'].search(
            [('type', '=', 'purchase'), ('company_id', '=', default_company_id)], limit=1)
        return journal.id

    def _get_default_deputation_ticket(self):
        default_company_id = self.env.company
        return default_company_id.deputation_ticket_product_id

    def _get_default_deputation_allowance_product_id(self):
        
        default_company_id = self.env.company
        return default_company_id.deputation_allowance_product_id

    name = fields.Char(string='Number#', default='New')
    employee_id = fields.Many2one('hr.employee', string='Employee', default=lambda self: self.env.user.employee_id)
    manager_id = fields.Many2one('hr.employee', related='employee_id.parent_id', string='Manager')
    department_id = fields.Many2one(related="employee_id.department_id",
                                    string='Department', store=True)
    job_title = fields.Char(related="employee_id.job_title", string='Job Title')
    description = fields.Html(string='Description')
    state = fields.Selection([('new', 'New'), 
                              ('direct_manager', 'Waiting Manager Approval'),
                              ('acceptance', 'Employee Acceptance'), 
                              ('hr', 'Waiting HR Officer Approval'),
                              ('hrm', 'Waiting HRM Approval'),
                              ('finance', 'Waiting For  Director of Financial and Administrative Affairs Approval'),
                              ('ceo', 'Waiting CEO Approval'),
                              ('to_pay', 'To Pay'),
                              ('paid', 'Paid'),
                              ('cancel', 'Canceled'), 
                              ('reject', 'Rejected')],
                             default='new', tracking=True)
    deputation_type = fields.Selection([('internal', 'Internal'), ('external', 'External')], default='internal',
                                       required=True)
    request_date = fields.Date(string='Request Date',
                               default=fields.Date.today()
                               )
    from_date = fields.Date(string='From')
    to_date = fields.Date(string='To')
    days = fields.Integer(string='Duration')
    travel_by = fields.Many2one('travel.way', string='Travel by')
    source_country_id = fields.Many2one('res.country', string='Country',
                                        default=lambda self: self.env.user.company_id.country_id)
    destination_country_id = fields.Many2one('res.country', string='Destination Country',
                                             domain="[('country_group_ids','in', country_group_id)]")
    from_city_id = fields.Many2one('res.city', 'From City')
    to_city_id = fields.Many2one('res.city', 'To City')
    deputation_id = fields.Many2one('deputation.cities.allowance', string='Business Trip', ondelete='restrict',
                                    domain="[('deputation_type','=', deputation_type)]")
    housing_by = fields.Selection([('by_company', 'By Company'), ('by_employee', 'By Employee'), ('without_overnight', 'Without overnight')],
        string='Housing By?', default='by_company')
    transportation_cost = fields.Selection([('by_company', 'By Company'), ('by_employee', 'Cash On Hand')],
                                           string='Transportation Cost?', default='by_company')

    allowance_ids = fields.One2many('hr.deputation.allowance.line', 'deputation_id', string='Allowance')
    deputation_amount = fields.Float('Total Amount')
    deputation_allowance = fields.Float('Basic Allowance')
    perdiem_amount = fields.Float(string='Per-Diem Amount')
    deputation_other_allowance = fields.Float('Other Allowance')
    daily_other_allowance = fields.Float('Other Allowance(Daily)')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)
    flight_ticket = fields.One2many('hr.flight.ticket', 'deputation_id',
                                    string='Flight Ticket', help="Flight ticket")
    need_ticket = fields.Boolean(related='travel_by.need_ticket', string='Need Ticket?')
    days_before = fields.Integer(string='Days Before', tracking=True)
    days_after = fields.Integer(string='Days After', tracking=True)
    total_days = fields.Integer(string='Total Days', compute='_compute_total_days')
    leave_type_id = fields.Many2one('hr.leave.type', string='Deputation Leave',
                                    default=lambda self: self.env.company.deputation_leave_type_id)
    deputation_ticket_product_id = fields.Many2one('product.product', string='Travel Ticket Product',
                                                   default=_get_default_deputation_ticket)
    deputation_allowance_product_id = fields.Many2one('product.product',  string='Deputation Allowance Product',
                                                      default=_get_default_deputation_allowance_product_id)
    deputation_analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account',
                                                     default=lambda
                                                         self: self.env.company.deputation_analytic_account_id)
    currency_id = fields.Many2one(related='company_id.currency_id', readonly=True)
    accounting_date = fields.Date("Accounting Date")
    journal_id = fields.Many2one('account.journal', string='Expense Journal',
                                 states={'done': [('readonly', True)], 'post': [('readonly', True)]},
                                 check_company=True,
                                 domain="[('type', '=', 'purchase'), ('company_id', '=', company_id)]",
                                 default=_default_journal_id, help="The journal used when the deputation is done.")
    account_move_id = fields.Many2one('account.move', string='Journal Entry', ondelete='restrict', copy=False,
                                      readonly=True)
    attachment_number = fields.Integer('Number of Attachments', compute='_compute_attachment_number')
    payment_ids = fields.One2many('account.payment', 'deputation_id', string='Payments')
    payment_amount = fields.Monetary('Payment Amount', compute='_calc_payment_amount', compute_sudo=True, store=True)
    country_group_id = fields.Many2one('res.country.group', string='Country Group',
                                       related='deputation_id.country_group_id', store=True)
    approval_ids = fields.One2many('hr.request.approvals', 'trip_id', string="Approver's")
    is_employee = fields.Boolean(compute='request_owner')
    current_user_id = fields.Many2one('res.users', compute='get_current_user')
    amount_residual = fields.Monetary(string='Amount Due', compute='_compute_amount_residual')
    from_portal = fields.Boolean("Created From Portal")
    is_manager = fields.Boolean(compute='get_current_uid')
    can_reject = fields.Boolean(compute='_compute_can_reject')

    def _compute_can_reject(self):
        if self.employee_id.user_id.id == self.env.user.id and self.state == 'acceptance':
            self.can_reject = True
        elif self.is_manager and self.state == 'direct_manager':
            self.can_reject = True
        elif self.state == 'hr' and self.env.user.has_group('plustech_hr_business_trip.group_hr_deputation_officer'):
            self.can_reject = True
        elif self.state == 'hrm' and self.env.user.has_group('plustech_hr_business_trip.group_hr_deputation_manager'):
            self.can_reject = True
        elif self.state == 'ceo' and self.env.user.has_group('plustech_hr_business_trip.group_hr_deputation_ceo'):
            self.can_reject = True

        else:
            self.can_reject = False

    @api.depends('manager_id')
    def get_current_uid(self):
        """

        :param self:
        :return:
        """
        if self.manager_id.user_id.id == self.env.user.id:
            self.is_manager = True
        else:
            self.is_manager = False

    @api.depends("account_move_id.line_ids")
    def _compute_amount_residual(self):
        for record in self:
            if not record.currency_id or record.currency_id == record.company_id.currency_id:
                residual_field = 'amount_residual'
            else:
                residual_field = 'amount_residual_currency'
            payment_term_lines = record.account_move_id.sudo().line_ids \
                .filtered(
                lambda line: line.deputation_id == record and line.account_internal_type in ('receivable', 'payable'))
            record.amount_residual = -sum(payment_term_lines.mapped(residual_field))

    @api.depends('current_user_id')
    def request_owner(self):
        for record in self:
            if record.current_user_id == record.employee_id.user_id:
                record.is_employee = True
            else:
                record.is_employee = False

    def get_current_user(self):
        for record in self:
            record.current_user_id = self.env.user

    # @api.depends('deputation_id')
    # def _get_country_group_id(self):
    #     for record in self:
    #         country_group_id = self.env['res.country.group'].search(
    #             [('country_ids', '=', record.to_city_id.country_id.id)], limit=1)
    #         record.country_group_id = country_group_id

    @api.depends('payment_ids.amount', 'payment_ids.currency_id', 'payment_ids.state')
    def _calc_payment_amount(self):
        for record in self:
            total_amount = 0
            for payment in record.payment_ids:
                if payment.state == 'cancelled':
                    continue
                amount = payment.with_context(date=payment.date).currency_id.compute(payment.amount, record.currency_id)
                if payment.payment_type == 'inbound':
                    amount = -amount
                total_amount += amount
            record.payment_amount = total_amount

    @api.depends('days_before', 'days_after', 'days')
    def _compute_total_days(self):
        for record in self:
            record.total_days = record.days_before + record.days_after + record.days

    @api.model
    def create(self, vals):
        
        if vals.get('name', _('New')) == _('New'):
            seq_date = None
            if 'request_date' in vals:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['request_date']))
            vals['name'] = self.env['ir.sequence'].next_by_code('business.trip', sequence_date=seq_date) or _('New')
        result = super(BusinessTripRequest, self).create(vals)
        return result

    def unlink(self):
        if any(self.filtered(lambda trip: trip.state not in ['new'])):
            raise UserError('You cannot delete a business trip which is not draft!')
        return super(BusinessTripRequest, self).unlink()

    @api.onchange('allowance_ids', 'deputation_allowance', 'total_days')
    def _onchange_allowance_ids(self):
        allowance = sum([line.amount for line in self.allowance_ids])
        self.deputation_other_allowance = allowance
        self.daily_other_allowance = allowance
        self.deputation_amount = self.deputation_other_allowance + self.deputation_allowance

    @api.onchange('from_date', 'to_date')
    def _compute_days(self):
        if self.from_date and self.to_date and self.from_date <= self.to_date:
            date_format = "%Y-%m-%d"
            start_date = datetime.strptime(str(self.from_date), date_format)
            end_date = datetime.strptime(str(self.to_date), date_format)
            duration = (end_date - start_date)
            self.days = int(duration.days)+1
            self._onchange_allowance_ids()

    @api.onchange('destination_country_id', 'deputation_id')
    def _onchange_country_id(self):
        domain = [('country_id', '=', self.destination_country_id.id),
                  ('id', 'not in', self.deputation_id.excluded_city_ids.ids)] if self.destination_country_id else []
        return {'domain': {'to_city_id': domain}}

    @api.onchange('deputation_type')
    def _onchange_deputation_type(self):
        if not 'active_model' in self._context or not self._context.get('active_model') == 'training.training':
            self.deputation_id = False
            if self.deputation_type == 'internal':
                self.destination_country_id = self.env.company.country_id.id
            else:
                self.destination_country_id = False
       
    @api.onchange('deputation_id')
    def onchange_deputation_id(self):
        self.days_before = self.deputation_id.days_before
        self.days_after = self.deputation_id.days_after

    @api.onchange('from_city_id', 'to_city_id', 'housing_by', 'deputation_id', 'employee_id', 'deputation_type', 'total_days')
    def _onchange_city_id(self):
        if self.from_city_id and self.to_city_id:
            deputation_allowance = self._get_allowance()
            self.deputation_allowance = deputation_allowance*self.total_days
            self.perdiem_amount = deputation_allowance

    def _get_allowance(self):
        allowance = self.deputation_id.allowance_ids.filtered(lambda line: self.employee_id.job_id.id in line.job_position_ids.ids)
        amount = allowance.per_diem_amount
        return amount

    def _compute_attachment_number(self):
        domain = [('res_model', '=', 'hr.deputation'), ('res_id', 'in', self.ids)]
        attachment_data = self.env['ir.attachment'].read_group(domain, ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for request in self:
            request.attachment_number = attachment.get(request.id, 0)

    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        res['domain'] = [('res_model', '=', 'hr.deputation'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'hr.deputation', 'default_res_id': self.id}
        return res

    def create_activity(self, state, user=False):
        business_trip_activity_obj = self.env['business.trip.activity'].sudo().search([('type','=','trip'),('business_trip_state', '=', state)])
        if business_trip_activity_obj:
            for obj in business_trip_activity_obj:
                self.env['mail.activity'].sudo().create({
                    'activity_type_id': obj.activity_type_id.id,
                    'res_id': self.id,
                    'res_model_id': self.env['ir.model'].sudo().search([('model', '=', 'hr.deputation')], limit=1).id,
                    'icon': 'fa-pencil-square-o',
                    'date_deadline': fields.Date.today(),
                    'user_id': user.id if user.id else obj.users_id.id,
                    'summary': obj.subject if obj.subject else False,
                    'note': obj.note,
                })

    def action_submit(self):
        if self.from_portal:
            self.write({'state': 'direct_manager'})
            self.create_activity(self.state, self.manager_id.user_id)
        if self.env.user == self.employee_id.user_id or self.env.user != self.manager_id.user_id:
            self.write({'state': 'direct_manager'})
            self.create_activity(self.state, self.manager_id.user_id)
        else:
            self.write({'state': 'acceptance'})
            self.create_activity(self.state, self.employee_id.user_id)

    def action_reject(self):
        self.write({'state': 'reject'})
        self.create_activity(self.state)


    def action_draft(self):
        self.write({'state': 'new'})
        self.create_activity(self.state)


    def _get_expense_account_source(self, product_id):
        self.ensure_one()

        if product_id:
            account = product_id.product_tmpl_id.with_company(self.company_id)._get_product_accounts()['expense']
            if not account:
                raise UserError(
                    _("No Expense account found for the product %s (or for its category), please configure one.") % (self.product_id.name))
        else:
            account = self.env['ir.property'].with_company(self.company_id)._get('property_account_expense_categ_id', 'product.category')
            if not account:
                raise UserError(_('Please configure Default Expense account for Category expense: `property_account_expense_categ_id`.'))
        return account

    def _get_expense_account_destination(self):
        self.ensure_one()
        if not self.employee_id.sudo().address_home_id:
            raise UserError(_("No Home Address found for the employee %s, please configure one.") % (self.employee_id.name))
        partner = self.employee_id.sudo().address_home_id.with_company(self.company_id)
        account_dest = partner.property_account_payable_id or partner.parent_id.property_account_payable_id
        return account_dest.id

    def _prepare_move_values(self):
        """
        This function prepares move values related to an expense
        """
        self.ensure_one()
        journal = self.journal_id
        account_date = self.accounting_date or self.to_date
        move_values = {
            'journal_id': journal.id,
            'company_id': self.company_id.id,
            'date': account_date,
            'ref': self.name,
            # force the name to the default value, to avoid an eventual 'default_name' in the context
            # to set it to '' which cause no number to be given to the account.move when posted.
            'name': '/',
        }
        return move_values

    def _get_account_move_line_values(self):
        move_line_values = {}
        for record in self:
            move_line_name = record.employee_id.name + ': ' + record.name.split('\n')[0][:64]
            account_date = self.accounting_date or record.to_date or fields.Date.context_today(record)
            deputation_allowance_product_id = record.deputation_allowance_product_id or self.company_id.deputation_allowance_product_id
            account_src = record._get_expense_account_source(deputation_allowance_product_id)
            account_dst = record._get_expense_account_destination()
            move_line_values = []
            unit_amount = record.deputation_allowance
            partner_id = record.employee_id.sudo().address_home_id.commercial_partner_id.id
            # source move line
            move_line_src = {
                'name': move_line_name,
                'quantity': 1,
                'debit':  unit_amount if unit_amount > 0 else 0,
                'credit': unit_amount < 0 and -unit_amount or 0,
                'account_id': account_src.id,
                'product_id': deputation_allowance_product_id.id,
                'product_uom_id': deputation_allowance_product_id.uom_id.id,
                'analytic_account_id': record.deputation_analytic_account_id.id,
                'deputation_id': record.id,
                'partner_id': partner_id,
                'currency_id': record.currency_id.id,
            }
            move_line_values.append((0,0,move_line_src))
            for allowance in self.allowance_ids:
                product_id = allowance.allowance_id.product_id
                account_src = record._get_expense_account_source(product_id)
                move_line_src = {
                    'name': move_line_name,
                    'quantity': 1,
                    'debit': allowance.amount if allowance.amount > 0 else 0,
                    'credit': allowance.amount < 0 and -allowance.amount or 0,
                    'account_id': account_src.id,
                    'product_id': product_id.id,
                    'product_uom_id': product_id.uom_id.id,
                    'analytic_account_id': record.deputation_analytic_account_id.id,
                    'partner_id': partner_id,
                    'deputation_id': record.id,
                    'currency_id': record.currency_id.id,
                }
                move_line_values.append((0, 0, move_line_src))
                unit_amount+=allowance.amount
            # destination move line
            move_line_dst = {
                'name': move_line_name,
                'debit': unit_amount < 0 and -unit_amount or 0,
                'credit': unit_amount > 0 and unit_amount or 0,
                'account_id': account_dst,
                'date_maturity': account_date,
                'currency_id': record.currency_id.id,
                'partner_id': partner_id,
                'deputation_id': record.id,
                'exclude_from_invoice_tab': True,
            }
            move_line_values.append((0,0,move_line_dst))

        return move_line_values

    def action_move_create(self):
        for record in self:
            move_vals = record._prepare_move_values()
            move_vals['line_ids'] = self._get_account_move_line_values()
            move = self.env['account.move'].with_context(default_journal_id=move_vals['journal_id']).create(move_vals)
            if move:
                record.account_move_id = move.id

    def action_register_payment(self):
        # ToDo :to enable payment wizard after implement accounting module
        #  <<remove update state and uncomment return wizard code>>
        self.write({'state': 'paid'})
        # return {
        #     'name': _('Register Payment'),
        #     'res_model': 'account.payment.register',
        #     'view_mode': 'form',
        #     'context': {
        #         'active_model': 'account.move',
        #         'active_ids': self.account_move_id.ids,
        #         'default_partner_bank_id': self.employee_id.sudo().bank_account_id.id,
        #         'default_deputation_id': self.id,
        #     },
        #     'target': 'new',
        #     'type': 'ir.actions.act_window',
        # }


    def action_open_account_move(self):
        self.ensure_one()
        return {
            'name': self.account_move_id.name,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.account_move_id.id
        }

    def action_generate_payment(self):
        result = self.env.ref('account.action_account_payments').read()[0]
        view_id = self.env.ref('account.view_account_payment_form').id
        result.update({'views': [(view_id, 'form')], })
        result['context'] = {
            'default_partner_id': self.employee_id.address_home_id.id,
            'default_payment_type': 'outbound',
            'default_amount': self.deputation_amount,
            'default_deputation_id': self.id,
            'default_communication': 'Business Trip %s' % self.name,
        }
        return result

    def action_payment_view(self):
        self.ensure_one()
        action, = self.env.ref('account.action_account_payments').read()
        action['domain'] = [('deputation_id', '=', self.id)]
        return action

    def book_ticket(self):
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_employee_id': self.employee_id.id,
            'default_deputation_id': self.id,
            'default_type': 'business_trip',
            'default_country_from_id': self.company_id.country_id.id,
            'default_country_to_id': self.destination_country_id.id,
            'default_city_from_id': self.from_city_id.id,
            'default_city_to_id': self.to_city_id.id,
            'default_date_start': self.from_date - timedelta(days=int(self.days_before)),
            'default_date_return': self.to_date + timedelta(days=int(self.days_after)),
        })

        return {
            'name': _('Book Flight Ticket'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref('plustech_hr_flight_ticket.view_book_flight_ticket_form').id,
            'res_model': 'hr.flight.ticket',
            'target': 'new',
            'context': ctx,
        }

    def view_flight_ticket(self):
        return {
            'name': _('Flight Ticket'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'hr.flight.ticket',
            'target': 'current',
            'res_id': self.flight_ticket[0].id,
        }

    def convert_gregorian_to_hijri(self, date):
        return convert_gregorian_to_hijri(date)


class DeputationAllowanceLines(models.Model):
    _name = 'hr.deputation.allowance.line'
    _description = 'Deputation Allowance Lines'

    allowance_id = fields.Many2one('hr.deputation.allowance', string='Name', ondelete='restrict',
                                   domain="[('id', 'not in', existing_allowance_ids)]")
    deputation_id = fields.Many2one('hr.deputation')
    amount = fields.Float()
    type = fields.Selection([('fixed', 'Fixed Amount'), ('percentage', 'Percentage')])
    existing_allowance_ids = fields.Many2many('hr.deputation.allowance', compute='_compute_existing_allowance_ids')

    @api.depends('allowance_id')
    def _compute_existing_allowance_ids(self):
        for record in self:
            record.existing_allowance_ids = record.deputation_id.allowance_ids.allowance_id

    @api.onchange('allowance_id')
    def _onchange_allowance_id(self):
        self.amount = self.allowance_id.amount if self.allowance_id.type == 'fixed' else \
            (self.deputation_id.deputation_allowance * self.allowance_id.amount) / 100
