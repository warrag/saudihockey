# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrPunishment(models.Model):
    _name = 'hr.punishment'
    _inherit = ['mail.thread']
    _description = 'Employee Penalty'

    name = fields.Char(string='Punish No.', readonly=True)
    violation_id = fields.Many2one('violation.violation', string='Violation', required=True)
    penalty_id = fields.Many2one('penalty.penalty', string='Penalty', required=True,
                                 domain="[('violation_id', '=', violation_id)]", check_company=True,)
    applied_date = fields.Date(string='Applied Date')
    declaration_date = fields.Date(string='Declaration Date', required=True, default=fields.Date.today())
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    manager_id = fields.Many2one('hr.employee', string='Manager', related='employee_id.parent_id')
    is_manager = fields.Boolean('is_manager', compute="compute_is_manager")
    department_id = fields.Many2one('hr.department', string='Department', related='employee_id.department_id',
                                    store=True)
    job_id = fields.Many2one(string='Job Title', related='employee_id.job_id', store=True)
    deduct = fields.Boolean(string='Deduct from Salary')
    ded_amount = fields.Float(string='Deduction Amount', tracking=True, compute="compute_deduction_amount",
                              readonly=False)
    salary_type = fields.Selection([('gross', 'Gross Salary'), ('basic', 'Basic Salary'),
                                    ('selected_allowance', 'Basic + Selected Allowances')])
    allowance_ids = fields.Many2many('employee.allowance.type', string='Allowances')
    deducted_amount = fields.Float(string='Deducted Amount', readonly=True)
    remaining_amount = fields.Float(string='Remaining Amount', compute='compute_remaining_amount')
    state = fields.Selection(
        [('draft', 'draft'), ('dm', 'Line Manager'), ('chairman', 'Chairman'), ('hrm', 'HRM'), ('done', 'Done'),
         ('ded', 'Deducted from Salary')],
        string='Status', default='draft', tracking=True)
    note = fields.Html(string='Notes', required=True)
    stage_id = fields.Many2one('penalty.stage', string='Stage', required=True, check_company=True,)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    employee_number = fields.Char(related='employee_id.employee_number')
    payslip_id = fields.Many2one('hr.payslip', string='Payslip')
    company_id = fields.Many2one(
        string='Company',
        comodel_name='res.company',
        required=True,
        default=lambda self: self.env.company
    )
    hr_punishment_id = fields.Many2one('hr.punishment')
    history_matching = fields.Boolean()
    history_ids = fields.One2many('hr.punishment', 'hr_punishment_id', string='History')

    @api.onchange('violation_id', 'penalty_id', 'stage_id')
    def _compute_history_matching(self):
        for line in self.history_ids:
            if self.violation_id and not self.hr_punishment_id:
                if self.violation_id == line.violation_id:
                    line.history_matching = True
                    if self.penalty_id:
                        if self.penalty_id == line.penalty_id:
                            line.history_matching = True
                        else:
                            line.history_matching = False
                    if self.stage_id:
                        if self.stage_id == line.stage_id:
                            line.history_matching = True
                        else:
                            line.history_matching = False
                else:
                    line.history_matching = False
            else:
                line.history_matching = False

    @api.depends('user_id')
    def compute_is_manager(self):
        for record in self:
            record.is_manager = False
            if record.manager_id.user_id.id == self.env.user.id:
                record.is_manager = True

    @api.depends('ded_amount', 'remaining_amount')
    def compute_remaining_amount(self):
        for record in self:
            record.remaining_amount = record.ded_amount - record.deducted_amount

    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].get('violation.violation') or ' '
        res = super(HrPunishment, self).create(values)
        return res

    def unlink(self):
        if any(self.filtered(lambda punishment: punishment.state not in ['draft'])):
            raise UserError('You cannot delete a punishment which is not draft or refused!')
        return super(HrPunishment, self).unlink()

    @api.onchange('penalty_id')
    def _get_stages_domain(self):
        self.stage_id = False
        domain = [('id', 'in', self.penalty_id.stage_ids.ids)]
        return {'domain': {'stage_id': domain}}

    def action_line_manager_approval(self):
        self.state = 'dm'

    def action_chairman_approval(self):
        self.state = 'chairman'

    def action_hrm_approval(self):
        self.state = 'hrm'

    def action_done(self):
        self.write({'state': 'done', 'applied_date': fields.Date.today()})

    @api.onchange('stage_id', 'employee_id')
    def _onchange_stage_id(self):
        self.salary_type = self.stage_id.salary_type
        if self.stage_id.allowance_ids:
            self.allowance_ids = self.stage_id.allowance_ids

    @api.depends('deduct', 'salary_type', 'allowance_ids', 'stage_id')
    def compute_deduction_amount(self):
        for record in self:
            ded_amount = 0.0
            if record.stage_id.salary_deduction:
                record.deduct = True
                if record.stage_id.deduct_amount > 0:
                    deduction_type = record.stage_id.deduction_type
                    wage = 0.0
                    if record.salary_type == 'gross':
                        if deduction_type == 'days':
                            wage = record.employee_id.sudo().contract_id.monthly_yearly_costs / 30 or 0.0
                        else:
                            wage = record.employee_id.sudo().contract_id.monthly_yearly_costs
                    elif record.salary_type == 'basic':
                        if deduction_type == 'days':
                            wage = record.employee_id.sudo().contract_id.wage / 30 or 0.0
                        else:
                            wage = record.employee_id.sudo().contract_id.wage
                    elif record.salary_type == 'selected_allowance':
                        allowance_id = self.env['hr.employee.allowance'].search([
                            ('allowance_type', 'in', record.allowance_ids.ids)])
                        wage = ((record.employee_id.sudo().contract_id.wage + sum(
                            allowance_id.mapped('allowance_amount'))))
                        wage = wage / 30 or 0.0
                    ded_amount = deduction_type == "fixed" and record.stage_id.deduct_amount or deduction_type == "days" \
                                      and record.stage_id.deduct_amount * wage or (
                                                  record.stage_id.deduct_amount * wage) / 100
            record.ded_amount = ded_amount

    @api.onchange('employee_id')
    def _get_employee_penalties_history(self):
        self.history_ids = False
        for rec in self:
            domain = [('employee_id', '=', rec.employee_id.id), ('state', '=', 'done')]
            history_list = self.env['hr.punishment'].search(domain)
            self.history_ids = history_list

    def action_inform_employee(self):
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = \
                ir_model_data._xmlid_lookup('plustech_hr_employee_penalty.email_template_employee_penalty_inform')[2]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data._xmlid_lookup('mail.email_compose_message_wizard_form')[2]
        except ValueError:
            compose_form_id = False
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'hr.punishment',
            'active_model': 'hr.punishment',
            'active_id': self.ids[0],
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'custom_layout': "mail.mail_notification_paynow",
            'force_email': True,
        })
        lang = self.env.context.get('lang')
        if {'default_template_id', 'default_model', 'default_res_id'} <= ctx.keys():
            template = self.env['mail.template'].browse(ctx['default_template_id'])
            if template and template.lang:
                lang = template._render_lang([ctx['default_res_id']])[ctx['default_res_id']]

        self = self.with_context(lang=lang)
        ctx['model_description'] = _('Penalty Inform')

        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }
