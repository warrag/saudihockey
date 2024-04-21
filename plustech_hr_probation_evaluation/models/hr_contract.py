# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta
from datetime import date
from odoo import api, fields, models, _


class HrContract(models.Model):
    _inherit = 'hr.contract'

    period_history_ids = fields.One2many('employee.trial.period.history', 'contract_id')
    is_trial_period = fields.Boolean(string='Is trial period', compute='trial_period')
    previous_evaluation_id = fields.Many2one('probation.evaluation', string='Previous Evaluation')

    @api.depends('trial_date_end')
    def trial_period(self):
        for record in self:
            today = date.today()
            if record.trial_date_end and record.trial_date_end > today:
                record.is_trial_period = True
            else:
                record.is_trial_period = False

            if not record.period_history_ids and record.trial_date_end:
                duration = record.trial_date_end - record.date_start
                line_dict = {
                    'start_date': record.date_start,
                    'end_date': record.trial_date_end,
                    'duration': duration.days,
                    'job_id': record.job_id.id
                }
                new_line = self.env['employee.trial.period.history'].new(line_dict)
                record.period_history_ids += new_line

    def probation_evaluation_reminder(self):
        contracts = self.env['hr.contract'].search([('is_trial_period', '=', True), ('state', '=', 'open')])
        for contract in contracts:
            probation_manager_notification = contract.company_id.probation_manager_notification
            if contract.trial_date_end:
                manager_notice_date = date.today() + relativedelta(days=probation_manager_notification)
                if manager_notice_date == contract.trial_date_end:
                    user = contract.employee_id.parent_id.user_id
                    if user:
                        self.make_activity(contract, user)

                probation_hr_notification = contract.company_id.probation_hr_notification
                hr_notice_date = date.today() + relativedelta(days=probation_hr_notification)
                if hr_notice_date == contract.trial_date_end:
                    group = self.env.ref('hr.group_hr_user').id
                    users = self.get_users(group)
                    for user in users:
                        if user:
                            self.make_activity(contract, user)

    def make_activity(self, contract, user):
        activity_values = {
            'activity_type_id': self.env.ref('plustech_hr_contract.mail_activity_probation_evaluation').id,
            'summary': 'Follow-up: probation evaluation reminder',
            'user_id': user.id,
            'res_id': contract.id,
            'res_model_id': self.env.ref('plustech_hr_contract.model_hr_contract').id
        }
        self.env['mail.activity'].create(activity_values)

    def get_users(self, group_id):
        user_ids = self.env['res.users'].search(
            [('groups_id', 'in', group_id), ('login', 'not in', ['admin', str(self.env.user.company_id.email)])])
        return user_ids


class EmployeeTrialPeriodHistory(models.Model):
    _name = 'employee.trial.period.history'
    _description = 'Trial Period History'

    contract_id = fields.Many2one('hr.contract')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    duration = fields.Integer(string='Duration')
    job_id = fields.Many2one('hr.job', string='Job Title')
