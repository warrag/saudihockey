from odoo import fields, models, api
from dateutil.relativedelta import relativedelta
from datetime import date


class HrLoan(models.Model):
    _inherit = 'hr.loan'
    _description = 'Description'

    eos_due = fields.Float(string='End Of Service Dues')

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        self.eos_due = self.cal_eos_provisions()
        res = super(HrLoan, self)._onchange_employee_id()
        return res

    def cal_eos_provisions(self):
        company_id = self.company_id
        reason_id = self.env['end.service.reason'].search(
            [('provision_calculatation', '=', True)], limit=1)
        period = relativedelta(date.today(), self.employee_id.join_date)
        years = period.years
        total_reward = 0.0
        contract_id = self.employee_id.contract_id
        gros_salary = sum([contract_id.get_allowance(line.allowance_type.code) for line in contract_id.allowance_ids])
        gros_salary = gros_salary + contract_id.wage
        line = reason_id.rule_id.sorted(key=lambda line: (
            line.period_from), reverse=False).filtered(lambda line: years <= line.period_to)
        if line:
            factor = line[0].eos_award
            if self.employee_id.join_date:
                days = (date.today() - self.employee_id.join_date).days
                year = round(days / company_id.days_per_year, 2)
                months_reward = (year * factor * gros_salary)
                total_reward = round(months_reward, 2)

        return total_reward

