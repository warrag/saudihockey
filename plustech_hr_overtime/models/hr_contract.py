from odoo import models, fields, api


class HrContractOvertime(models.Model):
    _inherit = 'hr.contract'

    over_hour = fields.Monetary('Hour Wage', compute='compute_overtime_wage', readonly=False)
    over_day = fields.Monetary('Day Wage', compute='compute_overtime_wage', readonly=False)

    @api.depends('wage', 'monthly_yearly_costs')
    def compute_overtime_wage(self):
        for record in self:
            hours_per_day = record.resource_calendar_id.hours_per_day
            days = record.company_id.overtime_cal_days
            hour_actual_wage = round(((record.monthly_yearly_costs / days) / hours_per_day), 2) or 0.0
            hour_basic_wage = round(((record.wage / days) / hours_per_day), 2) or 0.0
            record.over_hour = (hour_actual_wage + (hour_basic_wage * 50)/100)
            record.over_day = record.over_hour*hours_per_day

