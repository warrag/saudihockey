# -*- coding: utf-8 -*-
from datetime import date
from odoo import api, fields, models, _


class CancelRequest(models.Model):
    _name = 'cancel.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    _description = 'Insurance Request'

    name = fields.Char(string='Number#', default='New')
    employee_id = fields.Many2one(
        comodel_name='hr.employee', string='Employee', default=lambda self: self.env.user.employee_id)
    department_id = fields.Many2one(
        comodel_name='hr.department', string='Department', related="employee_id.department_id", readonly=False)
    job_id = fields.Many2one(comodel_name='hr.job', string='Job Title',
                             related="employee_id.job_id", readonly=False)
    request_date = fields.Date(string='Request Date', default=date.today())
    note = fields.Text(string='Notice')
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.user.company_id.id)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  readonly=True, default=lambda self: self.env.user.company_id.currency_id.id)
    policy_id = fields.Many2one(
        comodel_name='insurance.policy', string='Policy')
    afford_amount = fields.Float(string='Afford Amount')
    category_lines = fields.Many2many(
        comodel_name='policy.category.line', string='Details')
    insurance_id = fields.Many2one(
        comodel_name='insurance.request', string='Current Insurance', compute='get_current_categ_id')
    categ_id = fields.Many2one(
        comodel_name='policy.category', string='Category', related='insurance_id.categ_id')
    attachment_number = fields.Integer('Number of Attachments', compute='get_attachment_ids')
    color = fields.Integer(string='Color Index')

    @api.onchange('employee_id')
    def get_current_categ_id(self):
        objs = self.employee_id.insurance_ids
        current = [x for x in objs if x.state == 'done']
        if len(current) > 0:
            self.insurance_id = current[0].id
        else:
            self.insurance_id = False

    state = fields.Selection(string='State', selection=[
        ('draft', 'Draft'),
        ('hr', 'Hr'),
        ('hr_manager', 'Hr Manager Approval'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
    ], default='draft', tracking=True)

    def action_submit(self):
        self.state = 'hr'

    def action_manager(self):
        self.state = 'hr_manager'

    def action_cancel(self):
        self.state = 'cancel'

    def action_done(self):
        self.insurance_id.state = 'cancel'
        self.state = 'done'

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            seq_date = None
            if 'request_date' in vals:
                seq_date = fields.Datetime.context_timestamp(
                    self, fields.Datetime.to_datetime(vals['request_date']))
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'cancel.request', sequence_date=seq_date) or _('New')
        result = super(CancelRequest, self).create(vals)
        return result

    def action_send(self):
        ''' Opens a wizard to compose an email, with relevant mail template loaded by default '''
        self.ensure_one()
        template_id = self.env['ir.model.data']._xmlid_to_res_id(
            'plustech_hr_medical_insurance.medical_cancel_email_template', raise_if_not_found=False)
        template_id = self.env['mail.template'].search(
            [('id', '=', template_id)]).id
        attachment = self.get_attachment_ids()

        ctx = {
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
        }

        ctx = {
            'default_model': 'insurance.request',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_attachment_ids': attachment.ids,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'custom_layout': "mail.mail_notification_paynow",
            'proforma': self.env.context.get('proforma', False),
            'force_email': True,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    def attach_document(self, **kwargs):
        pass

    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id(
            'base.action_attachment')
        res['domain'] = [('res_model', '=', 'cancel.request'),
                         ('res_id', 'in', self.ids)]
        res['context'] = {
            'default_res_model': 'cancel.request', 'default_res_id': self.id}
        return res

    def get_attachment_ids(self):
        ids = self.env['ir.attachment'].search([('res_id', '=', self.id)])
        self.attachment_number = len(ids)

        return ids
