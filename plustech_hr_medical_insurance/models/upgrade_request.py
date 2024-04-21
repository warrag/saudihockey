# -*- coding: utf-8 -*-
from datetime import date
from odoo import api, fields, models, _


class UpgradeRequest(models.Model):
    _name = 'upgrade.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    _description = 'Insurance Request'

    name = fields.Char(string='Number#', default='New')
    employee_id = fields.Many2one(
        comodel_name='hr.employee', string='Employee', default=lambda self: self.env.user.employee_id)
    department_id = fields.Many2one(
        comodel_name='hr.department', string='Department', related="employee_id.department_id", readonly=False)
    job_id = fields.Many2one(comodel_name='hr.job', string='Job Title', related="employee_id.job_id", readonly=False)
    request_date = fields.Date(string='Request Date', default=date.today())
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.user.company_id.id)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  required=True, readonly=True,
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    insurance_id = fields.Many2one(comodel_name='insurance.request', string='Current Insurance')
    policy_id = fields.Many2one(comodel_name='insurance.policy', string='Policy')
    current_categ_id = fields.Many2one(comodel_name='policy.category', string='Current Category',
                                       compute="get_current_categ_id")
    categ_id = fields.Many2one(comodel_name='policy.category', string='New Category',
                               domain="[('policy_id','=', policy_id)]")
    afford_amount = fields.Float(string='Afford Amount', readonly=True)
    category_lines = fields.Many2many(comodel_name='policy.category.line', string='Details')
    color = fields.Integer(string='Color Index')

    @api.onchange('policy_id')
    def onchange_policy_id(self):
        domain = {'domain': {'categ_id': [('policy_id', '=', self.policy_id.id),
                                          ('id', '!=', self.current_categ_id.id)]}}
        return domain

    @api.onchange('employee_id')
    def _onchange_policy_id(self):
        return {'domain': {'insurance_id': [('id', 'in', self.employee_id.insurance_ids.ids)]},
                'value': {'insurance_id': False}}

    @api.onchange('employee_id')
    def get_current_categ_id(self):
        objs = self.employee_id.insurance_ids
        current = [x for x in objs if x.state == 'done']
        if len(current) > 0:
            self.current_categ_id = current[0].categ_id.id
        else:
            self.current_categ_id = False

    state = fields.Selection(string='State', selection=[
        ('draft', 'Draft'),
        ('hr', 'Hr'),
        ('hr_manager', 'Hr Manager Approval'),
        ('employee', 'Employee Approval'),
        ('done', 'Done'),
    ], default='draft', tracking=True)

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

    @api.onchange('categ_id')
    def get_afford_amount(self):
        current_amount = self.current_categ_id.amount
        new_amount = self.categ_id.amount
        if current_amount and new_amount:
            delta = float(new_amount) - float(current_amount)
            self.afford_amount = delta

    @api.onchange('categ_id')
    def action_get_category_lines(self):
        self.category_lines = False
        items = self.categ_id.line_ids.ids
        self.category_lines = items

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            seq_date = None
            if 'request_date' in vals:
                seq_date = fields.Datetime.context_timestamp(
                    self, fields.Datetime.to_datetime(vals['request_date']))
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'upgrade.request', sequence_date=seq_date) or _('New')
        result = super(UpgradeRequest, self).create(vals)
        return result
