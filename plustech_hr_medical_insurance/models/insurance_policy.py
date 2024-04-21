# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError


class InsurancePolicy(models.Model):
    _name = 'insurance.policy'
    _description = 'Insurance Policy'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', translate=True)
    number = fields.Char(string='Policy Number')
    partner_id = fields.Many2one(comodel_name='res.partner', string='Service Provider')
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    amount = fields.Monetary(string='Amount')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    beneficiary = fields.Integer(string='Beneficiaries')
    category_ids = fields.One2many(
        comodel_name='policy.category', inverse_name='policy_id', string='Categories')

    renew_date = fields.Date(string='Renewal Due On')
    payment_method = fields.Many2one('account.payment.term')
    agreement_id = fields.Many2one(
        comodel_name='purchase.requisition', string='')
    color = fields.Integer(string='Color Index')

    state = fields.Selection(string='State', selection=[
        ('draft', 'Draft'),
        ('done', 'Validate'),
        ('cancel', 'Cancel'),
        ('expired', 'Expired'),
    ], default='draft', tracking=True)

    @api.onchange('start_date', 'end_date')
    def _onchange_duration(self):
        if self.end_date:
            self.renew_date = self.end_date + relativedelta(days=1)

    def action_done(self):
        self.state = 'done'

    def action_cancel(self):
        self.state = 'cancel'

    def action_expired(self):
        self.state = 'expired'

    def action_create_po(self):
        product = self.env['product.product'].create({
            'name': str(self.number),
            'detailed_type': 'service',
        })
        po = self.env['purchase.requisition'].create({
            'vendor_id': self.partner_id.id,
            'type_id': 1,
            'ordering_date': fields.Date.today(),
            'policy_id': self.id,
            'line_ids': [(0, 0, {
                'product_id': product.id,
                'product_qty': 1.0,
                'qty_ordered': 1.0,
                'price_unit': self.amount,
            }
                          )],
        })
        self.agreement_id = po.id

    def action_view_devices(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Purchase Agreement'),
            'res_model': 'purchase.requisition',
            'view_mode': 'tree,form',
            'domain': [('policy_id', '=', self.id)],
        }

    def action_medical_insurance(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Medical Insurance'),
            'res_model': 'insurance.request',
            'view_mode': 'tree,form',
            'domain': [('policy_id', '=', self.id)],
        }


class InsurancePolicyCategory(models.Model):
    _name = 'policy.category'
    _description = 'Insurance Policy Category'

    policy_id = fields.Many2one(comodel_name='insurance.policy', string='')

    name = fields.Char(string='Name')
    amount = fields.Char(string='Amount')
    line_ids = fields.One2many(
        comodel_name='policy.category.line', inverse_name='category_id', string='Categories')
    is_basic = fields.Boolean('Is Basic Category')

    @api.constrains('is_basic')
    def _check_unique_basic(self):
        for line in self:
            lines = self.env['policy.category'].search(
                [('is_basic', '=', True), ('policy_id', '=', line.policy_id.id)])
            if len(lines) > 1:
                raise ValidationError(_('Basic category must be unique!'))


class PolicyCategoryLine(models.Model):
    _name = 'policy.category.line'
    _description = 'Insurance Policy Category Line'

    category_id = fields.Many2one(comodel_name='policy.category', string='')
    item = fields.Many2one(comodel_name='policy.category.item', string='item')
    amount = fields.Float(string='Amount')
    percentage = fields.Float(string='Percentage')


class PolicyCategoryItem(models.Model):
    _name = 'policy.category.item'
    _description = 'Insurance Policy Item'

    name = fields.Char(string='Name')
    description = fields.Text(string='Description')


class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'

    policy_id = fields.Many2one('insurance.policy')
