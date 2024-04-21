# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta


class SkipLoanInstallment(models.Model):
    _name = 'hr.skip.installment'
    _description = 'Skip Installment'
    _inherit = 'mail.thread'
    _order = 'name desc'

    @api.model
    def _get_employee(self):
        employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
        return employee_id

    @api.model
    def _get_default_user(self):
        return self.env.user

    name = fields.Char('Name', default='/')
    employee_id = fields.Many2one('hr.employee', string='Employee', required="1", default=_get_employee)
    department_id = fields.Many2one('hr.department', related='employee_id.department_id')
    manager_id = fields.Many2one('hr.employee', related='employee_id.parent_id', string='Manager')
    employee_number = fields.Char(related='employee_id.employee_number')
    loan_id = fields.Many2one('hr.loan', string='Loan', required="1")
    installment_id = fields.Many2one('hr.loan.line', string='Installment')
    date = fields.Date('Date', default=fields.date.today())
    user_id = fields.Many2one('res.users', string='User', default=_get_default_user)
    notes = fields.Text('Reason', required="1")
    hr_officer_id = fields.Many2one('hr.employee', string='HR Officer')
    skip_installment_url = fields.Char('URL', compute='get_url')
    skip_type = fields.Selection(selection=[('to_next', 'To Next Month'),('skip_all', 'Skip All'),
                                  ('split', 'Skip With Split')], string='Skip Type', default='to_next', required=True)
    hr_manager_id = fields.Many2one('hr.employee', string='HR Manager')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    state = fields.Selection([('draft', 'Draft'),
                              ('submit', 'To Confirm'),
                              ('confirm', 'Waiting For Approval'),
                              ('approve', 'Approved'),
                              ('reject', 'Reject'),
                              ('cancel', 'Cancel'), ], string='State', default='draft', track_visibility='onchange')

    def get_url(self):
        for installment in self:
            ir_param = self.env['ir.config_parameter'].sudo()
            base_url = ir_param.get_param('web.base.url')
            action_id = self.env.ref('plustech_hr_loan.action_skip_installment').id
            menu_id = self.env.ref('plustech_hr_loan.menu_skip_installment').id
            if base_url:
                base_url += '/web#id=%s&action=%s&model=%s&view_type=form&cids=&menu_id=%s' % (
                    installment.id, action_id, 'hr.skip.installment', menu_id)
            installment.skip_installment_url = base_url

    @api.constrains('installment_id')
    def _Check_skip_installment(self):
        if self.employee_id and self.installment_id:
            request_id = self.search([('employee_id', '=', self.employee_id.id),
                                      ('installment_id', '=', self.installment_id.id),
                                      ('state', 'in', ['draft', 'approve', 'confirm', 'done']), ('id', '!=', self.id)])
            request = len(request_id)
            if request > 0:
                raise ValidationError("This %s  installment of skip request has been %s state" % (
                    self.installment_id.name, request_id.state))

    def get_users(self, group_id):
        users_ids = self.env['res.users'].search(
            [('groups_id', '=', group_id)])
        return users_ids

    def action_send_request(self):
        group_id = self.env.ref('hr.group_hr_user').id
        user_ids = self.get_users(group_id)
        template_id = self.env.ref('plustech_hr_loan.loan_skip_hr_officer_confirm')
        mtp = self.env['mail.template']
        template_id = mtp.browse(template_id.id)
        for user in user_ids:
            if user.partner_id.email:
                email_values = {
                    'email_to':  user.partner_id.email,
                }
                template_id.send_mail(self.id, force_send=True, email_values=email_values)
        self.state = 'submit'

    def confirm_skip_installment(self):
        self.hr_officer_id = self.env.user.employee_id
        group_id = self.env.ref('hr.group_hr_manager').id
        user_ids = self.get_users(group_id)
        template_id = self.env.ref('plustech_hr_loan.skip_ins_hr_manager_approval')
        mtp = self.env['mail.template']
        template_id = mtp.browse(template_id.id)
        for user in user_ids:
            if user.partner_id.email:
                email_values = {
                    'email_to': user.partner_id.email,
                }
                template_id.send_mail(self.id, force_send=True, email_values=email_values)
        self.state = 'confirm'

    def officer_reject_skip_installment(self):
        employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
        self.hr_officer_id = employee_id and employee_id.id or False
        if self.employee_id.work_email and self.hr_officer_id:
            template_id = self.env.ref('plustech_hr_loan.hr_officer_reject_skip_installment')
            mtp = self.env['mail.template']
            template_id = mtp.browse(template_id.id)
            email_values = {
                'email_to': self.employee_id.work_email,
            }
            template_id.send_mail(self.id, force_send=True, email_values=email_values)

        self.state = 'reject'

    def hr_manager_reject_skip_installment(self):
        employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
        self.hr_manager_id = employee_id and employee_id.id or False
        if self.employee_id.work_email and self.hr_manager_id:
            template_id = self.env.ref('plustech_hr_loan.hr_manager_reject_skip_installment')
            mtp = self.env['mail.template']
            template_id = mtp.browse(template_id.id)
            email_values = {
                'email_to': self.employee_id.work_email,
            }
            template_id.send_mail(self.id, force_send=True, email_values=email_values)

            self.state = 'reject'

        self.state = 'reject'

    def approve_skip_installment(self):
        if self.skip_type =='to_next':
            date = self.installment_id.date
            date = date + relativedelta(months=1)
            self.installment_id.date = date
        elif self.skip_type == 'skip_all':
            for line in self.loan_id.loan_lines.filtered(lambda ins: ins.state == 'pending'):
                date = line.date
                date = date + relativedelta(months=1)
                line.date = date
        elif self.skip_type == 'split':
            installments = self.loan_id.loan_lines.filtered(lambda ins: ins.state == 'pending' and ins.date > self.installment_id.date)
            amount = self.installment_id.amount/len(installments)
            for installment in installments:
                installment_amount = installment.amount + amount
                installment.write({'amount': installment_amount})
            self.installment_id.state = 'cancel'

        employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
        self.hr_manager_id = employee_id and employee_id.id or False
        self.state = 'approve'

        template_id = self.env.ref('plustech_hr_loan.hr_manager_approved_skip_installment')
        mtp = self.env['mail.template']
        template_id = mtp.browse(template_id.id)
        email_values = {
            'email_to': self.employee_id.work_email,
        }
        template_id.send_mail(self.id, force_send=True, email_values=email_values)

    def cancel_skip_installment(self):
        self.state = 'cancel'

    def set_to_draft(self):
        self.state = 'draft'

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'hr.skip.installment') or '/'
        return super(SkipLoanInstallment, self).create(vals)

    def copy(self, default=None):
        if default is None:
            default = {}
        default['name'] = '/'
        return super(SkipLoanInstallment, self).copy(default=default)

    def unlink(self):
        for skp_installment in self:
            if skp_installment.state != 'draft':
                raise ValidationError(_('Skip Installment delete in draft state only !!!'))
        return super(SkipLoanInstallment, self).unlink()
