# -*- coding: utf-8 -*-


from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)


class AccountJournalTransfer(models.Model):
    _name = 'account.journal.transfer'
    _inherit = ['mail.thread']
    _order = 'id desc'

    @api.depends('from_journal', 'state')
    def get_transfer_from_check(self):
        j_obj = self.env['account.journal']
        for rec in self:
            if rec.from_journal:
                if j_obj.search([('transfer_user_ids', 'in', [self.env.user.id]), ('id', '=', rec.from_journal.id)]):
                    rec.transfer_from_check = True
                else:
                    rec.transfer_from_check = False
            else:
                rec.transfer_from_check = False

    @api.constrains('amount')
    def constrains_amount(self):
        for rec in self:
            if rec.petty_user_id.over_limit != True:
                if rec.amount > rec.petty_user_id.limit:
                    raise ValidationError(_("Amount Bigger Than User Limit"))

    @api.depends('to_journal', 'state')
    def get_receive_from_check(self):
        j_obj = self.env['account.journal']
        for rec in self:
            if rec.to_journal:
                if j_obj.search([('receive_user_ids', 'in', [self.env.user.id]), ('id', '=', rec.to_journal.id)]):
                    rec.receive_from_check = True
                else:
                    rec.receive_from_check = False
            else:
                rec.receive_from_check = False

    @api.model
    def create(self, vals):
        print(vals)
        petty_holder = self.env['petty.user'].browse(vals['petty_user_id'])

        if vals['other_running'] and petty_holder.manay_petty == False:
            raise ValidationError(_("You can't have more petty cash"))

        if vals['amount'] <= 0:
            raise ValidationError(_('Please add amount.'))

        if not petty_holder.over_limit:
            if vals['amount'] > petty_holder.limit:
                raise ValidationError(
                    _("Your requested amount is over the limit. We can't process this request"))

        # if petty_holder.
        vals['name'] = self.env['ir.sequence'].get(
            'account.journal.transfer') or '/'
        return super(AccountJournalTransfer, self).create(vals)

    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Create By', copy=False, default=lambda self: self.env.user)
    name = fields.Char('Name', default='/', track_visibility='onchange')
    note = fields.Text('Note', track_visibility='onchange')
    date = fields.Date(
        string='Date',
        default=fields.Date.context_today, track_visibility='onchange')
    amount = fields.Float(string='Amount', copy=False,
                          track_visibility='onchange')
    remaining_amount = fields.Float("Remaining", compute='_compute_remaining')
    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  required=True, default=lambda self: self.env.user.employee_id)
    parent_id = fields.Many2one('hr.employee', string='Employee', related='employee_id.parent_id')
    department_id = fields.Many2one(
        comodel_name="hr.department", string="Department", related='employee_id.department_id')
    job_id = fields.Many2one('hr.job', related='employee_id.job_id')
    work_phone = fields.Char(related='employee_id.work_phone')
    work_mobile = fields.Char(related='employee_id.mobile_phone')
    work_email = fields.Char(related='employee_id.work_email')
    state = fields.Selection(string='State', selection=[
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('officer', 'Officer Approved'),
        ('manger', 'Manager Approved'),
        ('finance', 'Finance Approved'),
        ('running', 'Running'),
        ('cancel', 'cancel'),
        ('done', 'Done'),
    ], default='draft', required=True, track_visibility='onchange')
    other_running = fields.Boolean('Other Running Petty?', store=1)

    petty_ids = fields.One2many(
        comodel_name='account.journal.transfer', inverse_name='petty_id', )
    petty_id = fields.Many2one('account.journal.transfer')

    def _get_petty_user_id(self):
        return self.env['petty.user'].sudo().search([('user_id', '=', self.env.user.id), ('state', '=', 'active')], limit=1)

    petty_user_id = fields.Many2one('petty.user')
    transfer_move_ids = fields.Many2many(
        'account.move', string="Moves", store=1, copy=False)
    reconcile_line_ids = fields.One2many(
        'petty_cash.reconcile.bill', 'petty_cash_id')

    @api.depends('reconcile_line_ids', 'reconcile_line_ids.amount')
    def _compute_remaining(self):
        for record in self:
            consumed_amount = sum(
                line.amount for line in record.reconcile_line_ids)
            record.remaining_amount = record.amount - consumed_amount

    @api.onchange('employee_id')
    def change_employee_id(self):
        for rec in self:
            transfer_ids = self.env['account.journal.transfer'].sudo().search([
                ('employee_id', '=', rec.employee_id.id),
                ('state', '=', 'running'),
            ])
            rec.other_running = True if len(transfer_ids) > 0 else False
            # rec.petty_ids = [(6, 0, transfer_ids.ids)]
            rec.petty_user_id = self.env['petty.user'].search(
                [('employee_id', '=', rec.employee_id.id)]).id or False

    def action_cancel(self):
        self.state = 'cancel'

    def action_submit(self):
        self.state = 'submit'

    def action_officer_approve(self):
        self.state = 'officer'

    def action_manger_approve(self):
        self.state = 'manger'

    def action_financial_approve(self):
        if not self.env.user.company_id.petty_journal_id:
            raise ValidationError(_('Enter Petty Journal In Settings'))
        # if not self.env.user.company_id.petty_journal_id.default_account_id:
        #     raise ValidationError(_('Enter Default Account For Petty Journal'))
        if not self.env.user.company_id.petty_transfer_account_id:
            raise ValidationError(
                _('Enter Petty Transfer Account In Settings'))
        if not self.env.user.company_id.petty_analytic_account_id:
            raise ValidationError(
                _('Enter Petty Analytic Account In Settings'))

        view = self.env.ref('plustech_petty_cash.wizard_financial_view_form')
        return {
            'name': _('Financial Approve'),
            'view_mode': 'form',
            'view_id': view.id,
            'res_model': 'account.transfer.wizard',
            'type': 'ir.actions.act_window',
            'context': {'default_res_id': self.id},
            'target': 'new'
        }

    def action_view_move(self):
        action = self.env.ref("account.action_move_journal_line").read()[0]
        action["domain"] = [("id", "=", self.transfer_move_ids.ids),
                            ('is_petty_cash_transfer', '=', True)]
        return action

    def action_view_payment(self):
        action = self.env.ref("account.action_move_journal_line").read()[0]
        action["domain"] = [
            ("id", "=", self.transfer_move_ids.ids), ('is_petty_cash_payment', '=', True)]
        return action

    def action_view_bills(self):
        action = self.env.ref("account.action_move_in_invoice_type").read()[0]
        action["domain"] = [
            ("id", "=", self.transfer_move_ids.ids), ('move_type', 'in', ['in_invoice'])]
        return action

    def action_accept(self):
        amount = self.amount
        move_line_name = _('Petty Cash Transfer For ') + \
            self.petty_user_id.employee_id.name or ''
        credit_vals = {
            'name': move_line_name,
            'account_id': self.env.user.company_id.petty_transfer_account_id.id,
            'date': datetime.today().date(),
            'currency_id': self.env.user.company_id.currency_id.id,
            'credit': amount > 0.0 and amount or 0.0,
            'debit': amount < 0.0 and -amount or 0.0,
            'analytic_account_id': self.petty_user_id.analytic_account_id.id,
        }
        debit_vals = {
            'name': move_line_name,
            'account_id': self.petty_user_id.employee_id.address_home_id.property_account_receivable_id.id,
            'partner_id': self.petty_user_id.employee_id.address_home_id.id,
            'currency_id': self.env.user.company_id.currency_id.id,
            'date': datetime.today().date(),
            'credit': amount < 0.0 and -amount or 0.0,
            'debit': amount > 0.0 and amount or 0.0,
            'analytic_account_id': self.petty_user_id.analytic_account_id.id,
        }
        move = self.env['account.move'].sudo().create({
            'ref': _('Accept Petty Cash') + ' ' + self.name,
            'journal_id': self.env.user.company_id.petty_journal_id.id,
            'is_petty_cash_transfer': True,
            'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
        })
        move.action_post()
        self.transfer_move_ids = [(4, move.id)]
        self.state = 'running'

    def action_draft(self):
        self.state = 'draft'


class PettyCashReconciledBills(models.Model):
    _name = 'petty_cash.reconcile.bill'

    move_id = fields.Many2one(
        'account.move', string='Bill', ondelete="cascade")
    move_date = fields.Date(string='Date', related='move_id.date')
    move_state = fields.Selection([], related='move_id.state')
    amount = fields.Float(string='Reconciled Amount')
    reconciliation_date = fields.Date(string='Reconciliation Date')
    petty_cash_id = fields.Many2one(
        'account.journal.transfer', string='Petty Cash', required=True)
