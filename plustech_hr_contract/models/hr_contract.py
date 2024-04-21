# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta
from datetime import datetime, date
from odoo.addons.plustech_hr_contract.models.num_to_text_ar import amount_to_text_arabic
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _

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

    template_id = fields.Many2one(
        'hr.contract.template', string='Contract Template')
    end_of_service = fields.Boolean(related='contract_type_id.end_of_service', string='Has end of service?')
    has_vacations = fields.Boolean(related='contract_type_id.has_vacations', string='Has vacations?')
    has_medical_insurance = fields.Boolean(related='contract_type_id.has_medical_insurance',
                                           string='Has medical insurance?')
    has_allowance = fields.Boolean(related='contract_type_id.has_allowance', string='Has allowance?')
    duration_type = fields.Selection(related='contract_type_id.duration_type',
                                     string='Duration Type')
    contract_duration = fields.Char('Duration', compute='_calc_contract_duration', store=True)

    @api.depends('date_start', 'date_end', 'employee_id')
    def _calc_contract_duration(self):
        for record in self:
            delta = relativeDelta(record.with_context(lan=self.env.lang).date_end, record.date_start)
            record.contract_duration = delta_desc(delta)

    @api.onchange('employee_id')
    def _onchange_company_id(self):
        self.name = self.employee_id.employee_number
        self.date_start = self.employee_id.join_date
        res = super(HrContract, self)._onchange_company_id()
        return res

    def update_contract(self):
        for rec in self:
            if rec.state in ['draft', 'open']:
                rec.write({
                    'department_id': rec.employee_id.department_id.id,
                    'job_id': rec.employee_id.job_id.id,
                })

    def action_contract_preview(self):
        return self.env.ref('plustech_hr_contract.action_report_contract').report_action(self)

    def get_render_template(self):
        if not self.template_id:
            raise UserError(_("Please Select contract print template"))
        rendered_content = self.env['hr.contract.template'].render_template(
            self.template_id.body,
            self.template_id.model_id.model,
            self._origin.id)
        return rendered_content

    @api.onchange('trial_date_end')
    @api.constrains('trial_date_end')
    def _onchange_trial_period(self):
        for rec in self:
            if rec.trial_date_end and rec.date_start:
                duration = (rec.trial_date_end - rec.date_start).days
                if duration > 90:
                    raise ValidationError(
                        _("The trial period should be no more than 90 days"))

    def get_date_hijri(self):
        day = self.date_start.day
        month = self.date_start.month
        year = self.date_start.year
        hijri_date = Gregorian(year, month, day).to_hijri()
        return hijri_date

    def get_contract_period(self):
        duration = relativedelta(self.date_end, self.date_start)
        years = "%s Years" % duration.years if duration.months == 0 else "%s Years and %s Month" % (
            duration.years, duration.months)
        months = "%s Month" % duration.months
        result = years if duration.years > 0 else months
        return result

    def amount_to_text_arabic(self, amount):
        return amount_to_text_arabic(amount, 'SAR')

    def _onchange_final_yearly_costs(self):
        pass
        return super(HrContract, self)._onchange_final_yearly_costs()

    def reminder(self, days, users, reminder_type):
        if reminder_type == 'contract_end':
            end_domain = [
                ('state', '=', 'open'),
                ('date_end', '<=', fields.Date.to_string(date.today() + relativedelta(days=days or 60))),
                ('date_end', '>=', fields.Date.to_string(date.today() + relativedelta(days=1))),
            ]
            contracts = self.search(end_domain)
            for con in contracts:
                users = con.employee_id.parent_id.user_id if users == 'manager' else users
                if users:
                    users and con.message_post(body=_(
                        'Contract %s will be end within %s days, so need to take action to renew contract' % (
                            con.name, days)), email_from=self.env.user.company_id.email,
                        partner_ids=[user.partner_id.id for user in users])
        elif reminder_type == 'trial_end':
            trial_domain = [
                ('state', '=', 'open'),
                ('trial_date_end', '<=', fields.Date.to_string(date.today() + relativedelta(days=days or 7))),
                ('trial_date_end', '>=', fields.Date.to_string(date.today() + relativedelta(days=1))),
            ]
            contracts = self.search(trial_domain)
            for con in contracts:
                users = con.employee_id.parent_id.user_id if users == 'manager' else users
                if users:
                    users and con.message_post(body=_(
                        'Contract %s will be complete trail period in %s' % (
                            con.name, con.trial_date_end)), email_from=self.env.user.company_id.email,
                        partner_ids=[user.partner_id.id for user in users])

    @api.model
    def update_state(self):
        contract_end_days_hr_reminder = int(self.company_id.contract_end_days_hr_reminder)
        if contract_end_days_hr_reminder > 0:
            users = self.env.ref('hr.group_hr_user').users
            self.reminder(days=contract_end_days_hr_reminder, users=users, reminder_type='contract_end')
        probation_hr_notification = int(self.company_id.probation_hr_notification)
        if probation_hr_notification > 0:
            users = self.env.ref('hr.group_hr_user').users
            self.reminder(days=probation_hr_notification, users=users, reminder_type='trial_end')

        probation_manager_notification = int(self.company_id.probation_manager_notification)
        if probation_manager_notification > 0:
            self.reminder(days=probation_manager_notification, users='manager', reminder_type='trial_end')

        contract_end_days_manager_reminder = int(self.company_id.contract_end_days_manager_reminder)
        if contract_end_days_manager_reminder > 0:
            self.reminder(days=contract_end_days_manager_reminder, users='manager', reminder_type='contract_end')

        contracts = self.search([
            ('state', 'in', ('open', 'pending')),
            ('date_end', '<=', fields.Date.to_string(date.today() + relativedelta(days=1))),
        ])
        contracts.write({'state': 'close'})
        # finished today contract will be auto renewal
        contracts = self.search([
            ('state', 'in', ('open', 'pending')),
            ('date_end', '<=', fields.Date.to_string(date.today())),
        ])
        contracts.write({'state': 'close'})
        self.search([('state', '=', 'draft'), ('kanban_state', '=', 'done'),
                     ('date_start', '<=', fields.Date.to_string(date.today()))]).write({'state': 'open'
                                                                                        })

        contract_ids = self.search([('date_end', '=', False), ('state', '=', 'close'), ('employee_id', '!=', False)])
        # Ensure all closed contract followed by a new contract have a end date.
        # If closed contract has no closed date, the work entries will be generated for an unlimited period.
        for contract in contract_ids:
            next_contract = self.search([
                ('employee_id', '=', contract.employee_id.id),
                ('state', 'not in', ['cancel', 'new']),
                ('date_start', '>', contract.date_start)
            ], order="date_start asc", limit=1)
            if next_contract:
                contract.date_end = next_contract.date_start - relativedelta(days=1)
                continue
            next_contract = self.search([
                ('employee_id', '=', contract.employee_id.id),
                ('date_start', '>', contract.date_start)
            ], order="date_start asc", limit=1)
            if next_contract:
                contract.date_end = next_contract.date_start - relativedelta(days=1)
        return True


class ResCompany(models.Model):
    _inherit = 'res.company'

    company_represantative_id = fields.Many2one(
        'hr.employee', string="Company Representative", help="The company's representative")
