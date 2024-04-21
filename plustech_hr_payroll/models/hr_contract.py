# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta
from datetime import date
from odoo import api, fields, models, _
from odoo.addons.plustech_hr_employee.models.hr_employee import is_leap_year


try:
    from hijri_converter import Gregorian, convert
except ImportError:
    pass


def relativeDelta(enddate, startdate):
    if not startdate or not enddate:
        return relativedelta()
    startdate = fields.Datetime.from_string(startdate)
    enddate = fields.Datetime.from_string(enddate) + relativedelta(days=1)
    return relativedelta(enddate, startdate)


def delta_desc(delta):
    res = []
    if delta.years:
        res.append('%s Years' % delta.years)
    if delta.months:
        res.append('%s Months' % delta.months)
    if delta.days:
        res.append('%s Days' % delta.days)
    return ', '.join(res)


class HrContract(models.Model):
    _inherit = 'hr.contract'

    @api.model
    def _get_default_allowance(self, struct_id=False):
        allowance = []
        allowance_id = self.env['employee.allowance.type'].search([('is_default', '=', True),
                                                                   ('struct_id', '=', struct_id or False)])
        for all in allowance_id:
            val = (0, 0, {'allowance_type': all.id, 'amount_select': all.amount_select, 'amount': all.amount})
            allowance.append(val)
        return allowance

    company_gosi_percentage = fields.Float(string='Company', tracking=True, help="Gosi Company Ratio")
    employee_gosi_percentage = fields.Float(string='Employee', tracking=True, help="Gosi Employee Ratio")
    gosi_company_deduction = fields.Float(string='Monthly Company Deduction', compute="compute_gosi", store=True)
    gosi_company_daily = fields.Float(string='Daily Company Deduction', compute="compute_gosi", store=True)
    gosi_employee_deduction = fields.Float(string='Monthly Employee Deduction', compute="compute_gosi", store=True)
    gosi_employee_daily = fields.Float(string='Daily Employee Deduction', compute="compute_gosi", store=True)
    allowance_ids = fields.One2many('hr.employee.allowance', 'contract_id',
                                    string='Allowances', default=_get_default_allowance, copy=True)
    struct_id = fields.Many2one('hr.payroll.structure', string='Salary Structure',
                                ondelete='restrict', required=True, domain="[('type_id', '=', structure_type_id)]")
    gois_line_ids = fields.One2many('gosi.daily.contribution', 'contract_id')
    has_allowance = fields.Boolean(related='contract_type_id.has_allowance', string='Has allowance?')

    @api.onchange('struct_id')
    def onchange_salary_structure(self):
        if self.struct_id:
            self.allowance_ids = None
            if self.has_allowance:
                self.allowance_ids = self._get_default_allowance(self.struct_id.id)

    @api.onchange('employee_id')
    def _onchange_company_id(self):
        self.get_employee_gosi()
        res = super(HrContract, self)._onchange_company_id()
        return res

    def get_employee_gosi(self):
        for contract in self:
            if contract.state in ['draft', 'open']:
                country_id = contract.employee_id.country_id
                company_gosi_percentage = sum([rec.percentage for rec in self.env['hr.employee.gosi'].search(
                    [('is_active', '=', True), ('country_ids', 'in', country_id.ids), ('gosi_type', '=', 'company')])])
                contract.company_gosi_percentage = company_gosi_percentage
                employee_gosi_percentage = sum([rec.percentage for rec in self.env['hr.employee.gosi'].search(
                    [('is_active', '=', True), ('country_ids', 'in', country_id.ids), ('gosi_type', '=', 'employee')])])
                contract.employee_gosi_percentage = employee_gosi_percentage
                # delete old lines
                contract.gois_line_ids.unlink()
                lines = []
                months = {'1': 31, '2': 28, '3': 31, '4': 30, '5': 31, '6': 30, '7': 31, '8': 31, '9': 30, '10': 31,
                          '11': 30, '12': 31}
                if is_leap_year(date.today().year):
                    months[2] = 29
                month_names = {'1': _('January'), '2': _('February'), '3': _('March'), '4': _('April'), '5': _('May'),
                               '6': _('June'), '7': _('July'), '8': _('August'), '9': _('September'), '10': _('October'),
                               '11': _('November'), '12': _('December')}
                for month in months:
                    allowance = contract.allowance_ids.filtered(lambda line: line.gosi_deduction).mapped('allowance_amount')
                    allowed_wage = contract.wage + sum(allowance)
                    gosi_company_daily = (self.get_max_salary_for_gosi(contract.wage, sum(allowance)) * contract.company_gosi_percentage) / 100
                    gosi_company_daily = gosi_company_daily / months[month]
                    gosi_employee_daily = (self.get_max_salary_for_gosi(contract.wage, sum(allowance)) * contract.employee_gosi_percentage) / 100
                    gosi_employee_daily = gosi_employee_daily / months[month]
                    lines.append((0, 0, {'month_char': month_names[str(month)], 'days': months[month],
                                         'gosi_company_daily': gosi_company_daily,
                                         'gosi_employee_daily': gosi_employee_daily,
                                         'sequence': month}))
                contract.write({'gois_line_ids': lines})

    def get_allowance(self, code, paid_days=None):
        amount = 0.0
        for rec in self:
            allowance_id = rec.allowance_ids.search(
                [('allowance_type.code', '=', code), ('contract_id', '=', rec.id)], limit=1)
            if allowance_id:
                if allowance_id.amount_select == 'percentage':
                    amount = (rec.wage * allowance_id.amount) / 100
                elif allowance_id.amount_select == 'fix':
                    amount = allowance_id.amount
            if paid_days:
                amount = (amount / 30) * paid_days if paid_days < 30 else amount

        return amount

    @api.depends('company_gosi_percentage', 'employee_gosi_percentage', 'wage', 'allowance_ids')
    def compute_gosi(self):
        for rec in self:
            working_days = rec.resource_calendar_id.month_work_days
            allowance = rec.allowance_ids.filtered(lambda line: line.gosi_deduction).mapped('allowance_amount')
            allowed_wage = rec.wage + sum(allowance)
            rec.gosi_company_deduction = (self.get_max_salary_for_gosi(rec.wage, sum(allowance)) * rec.company_gosi_percentage) / 100
            rec.gosi_company_daily = rec.gosi_company_deduction / working_days
            rec.gosi_employee_deduction = (self.get_max_salary_for_gosi(rec.wage, sum(allowance)) * rec.employee_gosi_percentage) / 100
            rec.gosi_employee_daily = rec.gosi_employee_deduction / working_days

    def _onchange_final_yearly_costs(self):
        pass
        return super(HrContract, self)._onchange_final_yearly_costs()

    @api.depends(lambda self: (
            'wage',
            'structure_type_id.salary_advantage_ids.res_field_id',
            'structure_type_id.salary_advantage_ids.impacts_net_salary',
            'allowance_ids.allowance_amount',
            *self._get_advantage_fields()))
    def _compute_final_yearly_costs(self):
        for contract in self:
            allowance = sum(round(line.allowance_amount, 0) for line in contract.allowance_ids)
            total_cost = contract._get_salary_costs_factor() * allowance + contract._get_advantages_costs() + contract._get_salary_costs_factor() * contract.wage
            contract.final_yearly_costs = total_cost


    def get_max_salary_for_gosi(self, wage, allowance):
        if (wage + allowance) < self.company_id.max_salary_for_gosi:
            return wage + allowance
        else: return self.company_id.max_salary_for_gosi