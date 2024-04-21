# -*- coding: utf-8 -*-

from datetime import date
from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError


class EmployeePromotion(models.Model):
    _name = 'employee.promotion'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'
    _description = 'Employee Promotion'

    name = fields.Char(string='Number#', default='New')
    employee_id = fields.Many2one(
        comodel_name='hr.employee', string='Employee', default=lambda self: self.env.user.employee_id)
    employee_number = fields.Char(related='employee_id.employee_number', string='employee Number')
    prev_department_id = fields.Many2one(
        comodel_name='hr.department', string='Previous Department', readonly=True)
    prev_job_id = fields.Many2one(comodel_name='hr.job', string='Previous Job Position', readonly=True)
    new_department_id = fields.Many2one(
        comodel_name='hr.department', string='Designation Department')
    new_job_id = fields.Many2one(comodel_name='hr.job', string='Designation Job Position')
    request_date = fields.Date(string='Request Date', default=date.today())
    note = fields.Text(string='Notice')
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company.id)

    currency_id = fields.Many2one('res.currency', string='Currency',
                                  required=True, readonly=True, compute="_default_currency", tracking=True)

    contract_id = fields.Many2one(
        comodel_name='hr.contract', string='Contract', related="employee_id.contract_id")
    salary = fields.Monetary( string='Previous Salary')
    promotion_type = fields.Selection([('permanent', 'Permanent'), ('temporary', 'Temporary')],
                                      string='Promotion Type', default='permanent', required=True)
    action_type = fields.Selection([('promotion', 'Promotion'),
                                    ('adjustment', 'Salary Adjustment'),
                                    ("allowance", "Annual Allowance"),
                                    ('increment', 'Salary Increment')], default='promotion',
                                   string='Type Of Action', required=True)

    effective_date = fields.Date(string='Effective Date', required=True)
    end_date = fields.Date(string='End Date')
    increment_type = fields.Selection(string='Increment Type', selection=[
        ('fixed', 'Fixed Amount'), ('percentage', 'Percentage'), ], default='fixed')
    amount = fields.Float(string='Amount')
    percentage = fields.Float(string='Percentage')
    expect_salary = fields.Float(
        string='Proposed Salary', compute="_get_new_salary")
    attachment = fields.Binary(string='Attachment', attachment=True)
    allow_approve = fields.Boolean(string='', compute="_get_users")
    state = fields.Selection(related="stage_id.state",
                             store=True, readonly=True)
    description = fields.Text(
        string='Justification', required=True
    )
    attachment_number = fields.Integer('Number of Attachments', compute='_compute_attachment_number')
    is_applied = fields.Boolean(string='Applied')
    temporary_ended = fields.Boolean(string='Temporary Ended')
    previews_position = fields.Text(string='Old Values', compute='compute_previews_position')
    new_position = fields.Text(string='New Values', compute='compute_new_position')

    @api.depends('prev_department_id', 'prev_job_id', 'salary')
    def compute_previews_position(self):
        for record in self:
            if record.action_type == 'promotion':
                previews_position = "Department: {} \n Job Position: {}".format(record.prev_department_id.name or '',
                                                                                record.prev_job_id.name or '')
            else:
                previews_position = "Salary: {}".format(record.salary or 0.0)
            record.previews_position = previews_position

    @api.depends('new_department_id', 'new_job_id', 'expect_salary')
    def compute_new_position(self):
        for record in self:
            if record.action_type == 'promotion':
                new_position = "Department: {} \n Job Position: {}".format(record.new_department_id.name or '',
                                                                           record.new_job_id.name or '')
            else:
                new_position = "Salary: {}".format(record.expect_salary or 0.0)
            record.new_position = new_position

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        self.prev_job_id = self.employee_id.job_id
        self.prev_department_id = self.employee_id.department_id
        self.salary = self.contract_id.wage

    @api.model
    def _get_default_stage_id(self):
        return self.env["res.partner.stage"].search(
            [("is_default", "=", True)], limit=1
        )

    @api.model
    def _read_group_stage_id(self, states, domain, order):
        return states.search([])

    stage_id = fields.Many2one(
        comodel_name="res.partner.stage",
        group_expand="_read_group_stage_id",
        default=_get_default_stage_id,
        copy=False,
        index=True,
        tracking=True,
    )
    state = fields.Selection(related="stage_id.state",
                             store=True, readonly=True)

    def _get_users(self):
        self.allow_approve = False
        if (self.env.user.id in self.stage_id.user_ids.ids and self.state == 'draft') or self.state == 'confirmed':
            self.allow_approve = True
        elif self.state != 'cancel':
            self.allow_approve = False

    def action_submit(self):
        if self.promotion_type == 'salary' and self.amount == 0:
            raise UserError(_('added amount or percentage must be grater than zero!'))
        if not self.contract_id:
            raise ValidationError(_("Employee not has running contract!"))
        next_code = int(self.stage_id.code) + 1
        next_stage = self.env["res.partner.stage"].search(
            [("code", "=", next_code)], limit=1)
        self.stage_id = next_stage.id

    def action_l_m_approve(self):
        self.state = 'l_m_approve'

    def action_hrm(self):
        self.state = 'hrm'

    def action_reject(self):
        self.state = 'reject'

    def action_done(self):
        body = "Dear %s\n %s" % (self.employee_id.name, self.description)
        self.employee_id.user_id.partner_id.message_post(
            body=body,
            message_type='notification',
            subtype_xmlid='mail.mt_note')
        # self.state = 'done'

    def _get_contract(self):
        if self.employee_id:
            contract = [
                x.id for x in self.employee_id.contract_ids if x.state == 'open']
            self.contract_id = contract[0]
        else:
            self.contract_id = False

    @api.depends('amount')
    def _get_new_salary(self):
        for record in self:
            if record.increment_type == 'fixed':
                record.expect_salary = record.salary + record.amount

            elif record.increment_type == 'percentage':
                record.expect_salary = record.salary + \
                                     (record.salary * record.amount / 100)
            else:
                record.expect_salary = record.salary

    @api.model
    def _default_currency(self):
        self.currency_id = self.env.user.company_id.currency_id.id

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            seq_date = None
            if 'request_date' in vals:
                seq_date = fields.Datetime.context_timestamp(
                    self, fields.Datetime.to_datetime(vals['request_date']))
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'Promotion.request', sequence_date=seq_date) or _('New')
        result = super(EmployeePromotion, self).create(vals)
        return result

    def unlink(self):
        if any(self.filtered(lambda record: record.state not in ['draft'])):
            raise UserError('You cannot delete promotion  which is not draft!')
        return super(EmployeePromotion, self).unlink()

    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        res['domain'] = [('res_model', '=', 'employee.promotion'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'employee.promotion', 'default_res_id': self.id}
        return res

    def _compute_attachment_number(self):
        attachment_data = self.env['ir.attachment'].read_group(
            [('res_model', '=', 'employee.promotion'), ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for record in self:
            record.attachment_number = attachment.get(record._origin.id, 0)

    def attach_document(self, **kwargs):
        pass

    @api.model
    def check_effective_date(self):
        to_applied_promotions = self.search([('effective_date', '<=', date.today()),
                                  ('is_applied', '=', False), ('state', '=', 'cancel')])

        for record in to_applied_promotions:
            if record.action_type == 'promotion':
                record.employee_id.department_id = record.new_department_id
                record.employee_id.job_id = record.new_job_id
                self._send_notification_email(record)
                record.is_applied = True
                record.employee_id.last_promotion_id = record.id
            else:
                record.employee_id.contract_id.wage = record.expect_salary
                record.is_applied = True
                self._send_notification_email(record)
                record.is_applied = True
                record.employee_id.last_promotion_id = record.id


        temp_end_promotions = self.search([('end_date', '<=', date.today()),('promotion_type', '=', 'temporary'),
                                             ('temporary_ended', '=', False), ('state', '=', 'cancel')])
        for temp in temp_end_promotions:
            if temp.action_type == 'promotion':
                temp.employee_id.department_id = temp.prev_department_id
                temp.employee_id.job_id = temp.previews_position
                temp.temporary_ended = True
            else:
                temp.employee_id.contract_id.wage = temp.salary
                temp.temporary_ended = True


    def _send_notification_email(self, record):
        notification_template_id = self.env.ref(
            "plustech_hr_promotion.mail_template_data_notification_employee_promotion").id
        record.with_context(force_send=True).sudo().message_post_with_template(int(notification_template_id),
                                                                               email_layout_xmlid='mail.mail_notification_light')
