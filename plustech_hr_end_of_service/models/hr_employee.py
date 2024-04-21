
from datetime import timedelta
from math import fabs

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    service_termination_date = fields.Date(
        string="Termination Date",
        groups="hr.group_hr_user",
        tracking=True,
        help=(
            "Termination date is the last day the employee actually works and"
            " this date is used for accrual leave allocations calculation"
        ),
    )
    service_duration = fields.Integer(
        string="Service Duration",
        groups="hr.group_hr_user",
        readonly=True,
        compute="_compute_service_duration",
        help="Service duration in days",
    )
    service_duration_years = fields.Integer(
        string="Service Duration (years)",
        groups="hr.group_hr_user",
        readonly=True,
        compute="_compute_service_duration_display",
    )
    service_duration_months = fields.Integer(
        string="Service Duration (months)",
        groups="hr.group_hr_user",
        readonly=True,
        compute="_compute_service_duration_display",
    )
    service_duration_days = fields.Integer(
        string="Service Duration (days)",
        groups="hr.group_hr_user",
        readonly=True,
        compute="_compute_service_duration_display",
    )

    @api.depends("join_date", "service_termination_date")
    def _compute_service_duration(self):
        for record in self:
            service_until = record.service_termination_date or fields.Date.today()
            if record.join_date and service_until > record.join_date:
                service_since = record.join_date
                service_duration = fabs(
                    (service_until - service_since) / timedelta(days=1)
                )
                record.service_duration = int(service_duration)
            else:
                record.service_duration = 0

    @api.depends("join_date", "service_termination_date")
    def _compute_service_duration_display(self):
        for record in self:
            service_until = record.service_termination_date or fields.Date.today()
            if record.join_date and service_until > record.join_date:
                service_duration = relativedelta(
                    service_until, record.join_date
                )
                record.service_duration_years = service_duration.years
                record.service_duration_months = service_duration.months
                record.service_duration_days = service_duration.days
            else:
                record.service_duration_years = 0
                record.service_duration_months = 0
                record.service_duration_days = 0

    def _get_date_start_work(self):
        return self.join_date or super()._get_date_start_work()

    def cal_eos_provisions(self, slip):
        company_id = self.company_id
        reason_id = self.env['end.service.reason'].search(
            [('provision_calculatation', '=', True)], limit=1)
        period = relativedelta(slip.date_to, self.join_date)
        years = period.years
        total_reward = 0.0
        contract_id = slip.contract_id
        gros_salary = sum([contract_id.get_allowance(line.allowance_type.code) for line in contract_id.allowance_ids])
        gros_salary = gros_salary+contract_id.wage
        line = reason_id.rule_id.sorted(key=lambda line: (
            line.period_from), reverse=False).filtered(lambda line: years <= line.period_to)
        if line:
            factor = line[0].eos_award
            if slip.date_from < self.join_date:
                days = (slip.date_to - self.join_date).days
                days+=1
            else:
                days = (slip.date_to - slip.date_from).days
                days+=1
            year= days/company_id.days_per_year
            months_reward = (year*factor*gros_salary)
            total_reward = round(months_reward, 2)

        return total_reward
