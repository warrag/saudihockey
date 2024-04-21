# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError,ValidationError


class HrEmployeeAllowance(models.Model):
    _name = 'hr.employee.allowance'
    _description = 'Employee Allowance'

    allowance_type = fields.Many2one('employee.allowance.type', string='Type', required=1,
                                     domain="[('id', 'not in', existing_allowance_ids)]"
                                     )
    amount = fields.Float(string='Amount')
    amount_select = fields.Selection([('fix', 'Fixed Amount'), ('percentage', 'Percentage(%)')])
    contract_id = fields.Many2one('hr.contract', string='Contract')
    allowance_amount = fields.Float(string='Allowance Amount', compute="_compute_final_amount",
                                    digits='Contract Allowance')
    gosi_deduction = fields.Boolean(string='Gosi Deduction', related='allowance_type.gosi_deduction')
    leave_compensation = fields.Boolean(string='Include In Leave Compensation', related='allowance_type.leave_compensation')
    existing_allowance_ids = fields.Many2many('employee.allowance.type', compute='_compute_existing_allowance_ids')

    @api.depends('allowance_type')
    def _compute_existing_allowance_ids(self):
        for record in self:
            record.existing_allowance_ids = record.contract_id.allowance_ids.allowance_type

    @api.onchange('amount')
    def _onchange_amount(self):
        if self.amount_select == "percentage":  # Case percent
            if self.amount > 100:
                raise UserError(_("The percentage must be not over 100"))

    @api.onchange('allowance_type')
    def _onchange_allowance_type(self):
        if self.allowance_type:
            self.amount_select = self.allowance_type.amount_select
            self.amount = self.allowance_type.amount

    @api.depends('amount', 'amount_select', 'contract_id.wage')
    def _compute_final_amount(self):
        amount = 0.0
        for rec in self:
            if rec.amount_select == 'fix':
                amount = rec.amount
            elif rec.amount_select == 'percentage':
                amount = (rec.contract_id.wage * rec.amount) / 100
            rec.allowance_amount = amount


class EmployeeAllowanceType(models.Model):
    _name = 'employee.allowance.type'
    _description = 'Allowance Type'

    name = fields.Char(string='Name', required=1, translate=True)
    code = fields.Char(string='Code', required=1)
    amount = fields.Float(string='Amount')
    is_default = fields.Boolean(string='Is Default')
    salary_rule_id = fields.Many2one('hr.salary.rule', 'Salary Rule')
    amount_select = fields.Selection([('fix', 'Fixed Amount'), ('percentage', 'Percentage(%)')], default='fix')
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company)
    struct_id = fields.Many2one('hr.payroll.structure', string='Salary Structure')
    create_rule = fields.Boolean(string='Create Rule', default=True)
    gosi_deduction = fields.Boolean(string='Gosi Deduction')
    leave_compensation = fields.Boolean(string='Include In Leave Compensation')
    category_id = fields.Many2one('hr.allowance.category', string='Category', required=True)

    # _sql_constraints = [
    #     (
    #         'code_unique',
    #         'UNIQUE(code)',
    #         _('Code must be unique!')
    #     )
    # ]

    @api.constrains('code')
    def _check_unique_code(self):
        for line in self:
            lines = self.env['employee.allowance.type'].search(
                [('id', '!=', line.id), ('code', '=', line.code), ('company_id', '=', line.company_id.id)])
            if lines:
                raise ValidationError(_('Code must be unique!'))

    @api.onchange('amount')
    def _onchange_amount(self):
        if self.amount_select == "percentage":  # Case percent
            if self.amount > 100:
                raise UserError(_("The percentage must be not over 100"))

    @api.model
    def create(self, vals_list):
        res = super(EmployeeAllowanceType, self).create(vals_list)
        if res.create_rule:
            rule_id = self.env['hr.salary.rule'].create(
                {'name': res.name,
                 'code': res.code,
                 'struct_id': res.struct_id.id,
                 'category_id': self.env['hr.salary.rule.category'].search([('code', '=', 'ALW')], limit=1).id,
                 'amount_select': 'code',
                 'amount_python_compute': "result = contract.get_allowance('%s')" % res.code,
                 'condition_select': 'python',
                 'condition_python': "result = contract.get_allowance('%s')" % res.code,
                 }
            )
            res.update({'salary_rule_id': rule_id.id})
        return res


class HrAllowanceCategory(models.Model):
    _name = 'hr.allowance.category'
    _description = 'Allowance Category'

    name = fields.Char(string='Name', translate=True)
    code = fields.Char(string='Code')

