# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta


class HrEmployeeExpense(models.Model):
    _name = 'hr.employee.expense'
    _description = 'Employee Expense'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _check_company_auto = True

    name = fields.Char(string='Number#', default='New')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, index=True, tracking=True)
    employee_number = fields.Char(related='employee_id.employee_number', string='Employee Number')
    request_date = fields.Date(string='Request Date', default=fields.Date.today())
    effective_date = fields.Date(string="Effective", tracking=True)
    end_date = fields.Date(string="End Date")
    interval_period = fields.Integer(string='Period(Months)')
    amount = fields.Float(string="Amount")
    state = fields.Selection([
        ('draft', 'Draft'), ('submit', 'Submitted'),
        ('confirm', 'Confirmed'), ('approve', 'Approved')
    ], string='Status', readonly=True, tracking=True, copy=False, default='draft')
    department_id = fields.Many2one('hr.department', related='employee_id.department_id', string='Department')
    job_id = fields.Many2one('hr.job', related='employee_id.job_id', string='Job Position')
    expense_type_id = fields.Many2one('hr.expense.type', string="Expense type")
    partner_id = fields.Many2one('res.partner', string="Contact")
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company)
    export_as = fields.Selection([('bill', 'Bill'), ('deferred', 'Deferred')],
                                 string='Export AS', related="expense_type_id.export_as", required=True)
    product_id = fields.Many2one('product.product', related="expense_type_id.product_id", string="Expense Product",
                                 domain="[('detailed_type', '=', 'service')]", readonly=False)
    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account",
                                          related="expense_type_id.analytic_account_id"
                                          )
    analytic_tag_id = fields.Many2one('account.analytic.tag', string="Analytic Tag",
                                      related="expense_type_id.analytic_tag_id")
    account_move_id = fields.Many2one('account.move', string='Bill', ondelete='restrict', copy=False,
                                      readonly=True)

    @api.onchange('effective_date', 'interval_period')
    def change_end_date(self):
        if self.effective_date:
            self.end_date = self.effective_date + relativedelta(months=self.interval_period, days=-1)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            seq_date = None
            if 'request_date' in vals:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['request_date']))
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.employee.expense', sequence_date=seq_date) or _(
                'New')
        result = super(HrEmployeeExpense, self).create(vals)
        return result

    def action_submit(self):
        self.write({'state': 'submit'})

    def action_confirm(self):
        self.write({'state': 'confirm'})

    def action_approve(self):
        self.write({'state': 'approve'})

    def action_create_deferred_expense(self):
        return True

    def action_create_payment(self):
        for record in self:
            move_vals = record._prepare_move_values()
            move_vals['invoice_line_ids'] = self._get_move_line_values()
            AccountMove = self.env['account.move'].with_context(default_move_type='in_invoice')
            move = AccountMove.with_company(move_vals['company_id']).create(move_vals)
            if move:
                record.account_move_id = move.id

    def _prepare_move_values(self):
        """
        This function prepares move values related to an expense
        """
        self.ensure_one()
        journal = self.env['account.move'].with_context(default_move_type='in_invoice')._get_default_journal()
        if not journal:
            raise UserError(_('Please define an accounting purchase journal for the company %s (%s).') % (
                self.company_id.name, self.company_id.id))
        account_date = self.effective_date
        move_values = {
            'journal_id': journal.id,
            'company_id': self.company_id.id,
            'date': account_date,
            'move_type': 'in_invoice',
            'invoice_user_id': self.env.user.id,
            'partner_id':  self.partner_id.address_get(['invoice'])['invoice'],
            'ref': self.name,
            'invoice_line_ids': [],
            'company_id': self.company_id.id,
            'name': '/',
        }
        return move_values

    def _get_move_line_values(self):
        self.ensure_one()
        move_line_values = [(0, 0, {
            'name': '%s: %s' % (self.expense_type_id.name, self.name),
            'product_id': self.product_id.id,
            'product_uom_id': self.product_id.uom_id.id,
            'quantity': 1,
            'price_unit': self.amount,
            'analytic_account_id': self.analytic_account_id.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_id.ids)],
        })]
        return move_line_values

    def action_open_account_move(self):
        self.ensure_one()
        return {
            'name': self.account_move_id.name,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.account_move_id.id,
            'context': {'create': 0}
        }
