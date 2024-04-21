# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class HrContract(models.Model):
    _inherit = 'hr.contract'

    state = fields.Selection(selection_add=[('partial', 'Partial Stop')])
    annual_leave_balance = fields.Integer(
        string='Annual Leave Balance',
        default=30

    )
    balance_cal_method = fields.Selection(
        string='Allocation Method',
        selection=[('daily', 'Daily'), ('monthly', 'Monthly'), ('yearly', 'Yearly')], default='yearly',
        help=""
    )
    monthly_balance = fields.Float(string='Monthly Balance', default=(21 / 12))
    daily_balance = fields.Float(string='Daily Balance', default=(21 / 12) / 30)
    timeoff_auto_allocation = fields.Boolean(string='TimeOff Auto Allocation?')
    contract_period = fields.Selection([('one_year', 'One Year'),
                                        ('two_year', 'Two Year'),
                                        ], string='Contract Period', default='one_year')
    deserved_leave = fields.Selection([('one_year', 'One Year'),
                                       ('two_year', 'Two Year'),
                                       ], string='Deserved Leave', default='one_year')
    leaves_plan_id = fields.Many2one('hr.leave.accrual.plan', string='Leave Balance Plan')

    @api.onchange('annual_leave_balance', 'balance_cal_method')
    def _onchange_annual_leave_balance(self):
        if self.balance_cal_method == 'monthly':
            self.monthly_balance = self.annual_leave_balance / 12
        elif self.balance_cal_method == 'daily':
            self.daily_balance = (self.annual_leave_balance / 12) / 30

    def auto_timeoff_allocation(self):
        context = self.env.context.copy()
        if 'from_allocation_cron' not in context:
            context.update({'from_allocation_cron': False})

        all_contracts = self.env['hr.contract'].search([('timeoff_auto_allocation', '=', True)])
        contracts = all_contracts if context['from_allocation_cron'] else self
        for rec in contracts:
            if not rec.leave_allocation_id:
                auto_allocation = self.company_id.hr_contract_timeoff_auto_allocation
                if rec.timeoff_auto_allocation:
                    time_off_type = self.env['hr.leave.type'].search([('is_annual_leave', '=', True)], limit=1)
                    if not time_off_type:
                        raise ValidationError(_("Please Set annual leave type!"))
                    balance = self.annual_leave_balance
                    if rec.balance_cal_method == 'monthly':
                        balance = self.monthly_balance
                    elif rec.balance_cal_method == 'daily':
                        balance = self.daily_balance
                    from_date = fields.Date.today()
                    to_date = from_date + relativedelta(months=12)
                    print(rec.employee_id.name)
                    records = self.env['hr.leave.allocation'].create({
                        'name': time_off_type.name,
                        'employee_id': rec.employee_id.id,
                        'employee_ids': [(6,0, rec.employee_id.ids)],
                        'number_of_days': 0,
                        'holiday_status_id': time_off_type.id,
                        'allocation_type': 'accrual',
                        'accrual_plan_id': rec.leaves_plan_id.id,
                        'holiday_type': 'employee',
                        'date_from': from_date,
                        'state': 'confirm',
                        'notes': _('Allocation automatically created from Contract Signature.'),
                    })
                    self.leave_allocation_id = records[0]
            if context['from_allocation_cron'] and rec.leave_allocation_id.state == 'validate':
                new_balance = rec.monthly_balance if rec.balance_cal_method == 'monthly' else rec.daily_balance
                duration = rec.leave_allocation_id.number_of_days + new_balance
                rec.leave_allocation_id.write({'number_of_days': duration})

    def write(self, vals):
        res = super().write(vals)
        contract_id = self.search([('employee_id', '=', self.employee_id.id), '|',
                                   ('state', '=', 'close'), ('state', '=', 'open')
                                   ], order='id asc', limit=1)
        if contract_id and not contract_id.employee_id.join_date:
            contract_id.employee_id.join_date = contract_id.date_start
        if 'state' in vals and vals['state'] == 'cancel':
            for record in self.filtered(lambda r: r.leave_allocation_id and r.leave_allocation_id.state != 'refuse'):
                record.leave_allocation_id.write({'state': 'refuse'})
                record.leave_allocation_id.message_post(
                    body=_('Contract has been cancelled.'),
                )
        elif 'state' in vals and vals['state'] == 'open':
            self.auto_timeoff_allocation()
        return res

    @api.model
    def create(self, values):
        res = super(HrContract, self).create(values)
        contract_id = self.search([('employee_id', '=', values['employee_id']), '|',
                                   ('state', '=', 'close'), ('state', '=', 'open')
                                   ], order='id asc', limit=1)
        if contract_id:
            contract_id.employee_id.join_date = contract_id.date_start
        return res


class ContractHistory(models.Model):
    _inherit = 'hr.contract.history'

    state = fields.Selection(selection_add=[('partial', 'Partial Stop')])
