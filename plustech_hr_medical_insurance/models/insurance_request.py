# -*- coding: utf-8 -*-
from datetime import date
from odoo import api, fields, models, _


class InsuranceRequest(models.Model):
    _name = 'insurance.request'
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
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  required=True, readonly=True, default=lambda self: self.env.user.company_id.currency_id.id)
    policy_id = fields.Many2one(
        comodel_name='insurance.policy', string='Policy')
    categ_id = fields.Many2one(
        comodel_name='policy.category', string='Category')
    afford_amount = fields.Float(string='Afford Amount')
    category_lines = fields.Many2many(
        comodel_name='policy.category.line', string='Details')
    up_categ_id = fields.Many2one(
        comodel_name='policy.category', string='New Category')
    show_up_categ = fields.Boolean(string='', default=False)

    po_id = fields.Many2one(comodel_name='purchase.order', string='')

    family_ids = fields.Many2many('hr.employee.family', string='Family',
                                  domain="[('employee_id', '=', employee_id)]")
    show_fam = fields.Boolean(string='', compute='_compute_show_fam',default=False)
    attachment_number = fields.Integer('Number of Attachments', compute='get_attachment_ids')
    color = fields.Integer(string='Color Index')
    bill_id = fields.Many2one('account.move', 'Bill')

    @api.depends('show_fam')
    def _compute_show_fam(self):
        if self.env.company.include_family:
            self.show_fam = True
        else:
            self.show_fam = False

    @api.onchange('up_categ_id')
    def get_afford_amount(self):

        current_amount = self.categ_id.amount
        new_amount = self.up_categ_id.amount
        if current_amount and new_amount:
            delta = float(new_amount) - float(current_amount)
            self.afford_amount = delta

    @api.onchange('policy_id')
    def _onchange_policy_id(self):
        self.categ_id = self.env['policy.category'].search([('is_basic', '=', True), ('policy_id', '=', self.policy_id.id)])
        return {'domain': {'categ_id': [('policy_id', '=', self.policy_id.id)]},
                'value': {'categ_id': False}}

    @api.onchange('employee_id')
    def _get_famity(self):

        ids = self.employee_id.fam_ids.ids
        return {'domain': {'family_ids': [('id', 'in', ids)]},
                'value': {'family_ids': False}}

    def action_send(self):
        """ Opens a wizard to compose an email, with relevant mail template loaded by default """
        self.ensure_one()
        template_id = self.env['ir.model.data']._xmlid_to_res_id(
            'plustech_hr_medical_insurance.medical_insu_email_template', raise_if_not_found=False)
        template_id = self.env['mail.template'].search([('id', '=', template_id)]).id
        attachment = self.get_attachment_ids()
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

    state = fields.Selection(string='State', selection=[
        ('draft', 'Draft'),
        ('hr', 'Hr'),
        ('hr_manager', 'Hr Manager Approval'),
        ('employee', 'Employee Approval'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
    ], default='draft',tracking=True)

    def action_submit(self):
        self.state = 'hr'

    def action_manager(self):
        self.state = 'hr_manager'

    def action_employee_approval(self):
        self.state = 'employee'

    def action_done(self):
        self.state = 'done'

    def action_upgrade_request(self):
        self.state = 'draft'
        self.show_up_categ = True

    def action_upgrade_open(self):

        return {
            'type': 'ir.actions.act_window',
            'name': _('Upgrade Request'),
            'res_model': 'upgrade.request',
            'view_mode': 'form',
            'context': {'default_employee_id': self.employee_id.id,
                        'default_policy_id': self.policy_id.id},
        }

    @api.onchange('categ_id', 'up_categ_id')
    def action_get_category_lines(self):
        self.category_lines = False
        if self.up_categ_id:
            items = self.up_categ_id.line_ids.ids
            self.category_lines = items
        else:
            items = self.categ_id.line_ids.ids
            self.category_lines = items

    def action_create_po(self):
        product = self.env['product.product'].create({
            'name': str(self.name),
            'detailed_type': 'service',
        })
        po = self.env['purchase.order'].create({
            'partner_id': self.policy_id.partner_id.id,
            'requisition_id':  self.policy_id.agreement_id.id,
            'date_order': fields.Date.today(),
            'order_line': [(0, 0, {
                'product_id': product.id,
                'product_qty': 1.0,
                'price_unit': float(self.categ_id.amount) + float(self.afford_amount)}
            )],
        })

        self.po_id = po.id

    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        res['domain'] = [('res_model', '=', 'insurance.request'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'insurance.request', 'default_res_id': self.id}
        return res

    def get_attachment_ids(self):
        ids = self.env['ir.attachment'].search([('res_id','=',self.id)])
        self.attachment_number = len(ids)

        return ids

    def attach_document(self, **kwargs):
        pass

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            seq_date = None
            if 'request_date' in vals:
                seq_date = fields.Datetime.context_timestamp(
                    self, fields.Datetime.to_datetime(vals['request_date']))
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'insurance.request', sequence_date=seq_date) or _('New')
        result = super(InsuranceRequest, self).create(vals)
        return result

    def action_create_bill(self):
        product = self.company_id.medical_insurance_product_id
        bill = self.env['account.move'].create({
            'partner_id': self.policy_id.partner_id.id,
            'move_type': 'in_invoice',
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'product_id': product.id,
                'quantity': 1.0,
                'price_unit': float(self.categ_id.amount) + float(self.afford_amount)}
                            )],
        })

        self.bill_id = bill.id

    def project_bills_view(self):
        action = self.env["ir.actions.actions"]._for_xml_id('account.action_move_in_invoice_type')
        action['domain'] = [('id', '=', self.bill_id.id), ('move_type', '=', 'in_invoice')]
        action.update({'context': {'create': False}})
        return action

