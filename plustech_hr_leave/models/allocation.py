from odoo import fields, models, api, _
from dateutil.relativedelta import relativedelta
from datetime import timedelta
from collections import defaultdict
from odoo.tools.date_utils import get_timedelta


class HrLeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'
    _description = 'Description'

    def _default_holiday_status_id(self):
        
        if self.user_has_groups('hr_holidays.group_hr_holidays_user'):
            domain = [('has_valid_allocation', '=', True), ('requires_allocation', '=', 'yes')]
        else:
            domain = [('has_valid_allocation', '=', True), ('requires_allocation', '=', 'yes'), ('employee_requests', '=', 'yes')]

        if self._context.get('default_plus_type') == 'leave':
            domain.append(('plus_type', '=', 'leave'))
        else:
            domain.append(('plus_type', '=', 'permission'))
        return self.env['hr.leave.type'].search(domain, limit=1)

    def _domain_holiday_status_id(self):
        domain = []
        
        if self.user_has_groups('hr_holidays.group_hr_holidays_user'):
            return domain
        
        if self._context.get('default_plus_type') == 'leave':
            return [('employee_requests', '=', 'yes'), ('plus_type', '=', 'leave')]
        else:
            return [('employee_requests', '=', 'yes'), ('plus_type', '=', 'permission')]
        

    holiday_status_id = fields.Many2one(
            "hr.leave.type", compute='_compute_holiday_status_id', store=True, string="Time Off Type", required=True, readonly=False,
            states={'cancel': [('readonly', True)], 'refuse': [('readonly', True)], 'validate1': [
                ('readonly', True)], 'validate': [('readonly', True)]},
            domain=_domain_holiday_status_id,
            default=_default_holiday_status_id)

            
    plus_type = fields.Selection(string='Type', selection=[
        ('permission', 'Permission'),
        ('leave', 'Leave'), ], required=True, default='leave')

    last_allocation_date = fields.Date()
    allocated_until = fields.Date()
    expiry_date = fields.Date()
    available_from = fields.Date()
    is_carry_forward = fields.Boolean(string='Is Carry Forward?')
    transferred = fields.Boolean(string='Transferred')
    cumulative_balance = fields.Boolean(string='Cumulative Balance',
                                        help='count cumulative balance from employee join date')
    from_join_date = fields.Boolean(compute='compute_from_date')

    @api.depends('cumulative_balance')
    def compute_from_date(self):
        for record in self:
            if record.cumulative_balance and record.employee_id:
                record.date_from = record.lastcall = record.employee_id.join_date - relativedelta(days=1)
                record.from_join_date = True
            else:
                record.from_join_date = False

    def name_get(self):
        if not self._context.get('is_balance'):
            return super(HrLeaveAllocation, self).name_get()
        res = []
        for record in self:
            name = record.name
            res.append((record.id, name))
        return res

    def _end_of_validity_period(self):
        today = fields.Date.today()
        allocation = self.env['hr.leave.allocation'].search([('date_to', '=', today), ('transferred', '=', False)])
        for rec in allocation:
            number_of_days = rec.number_of_days - rec.leaves_taken
            date_from = rec.date_from.replace(year=today.year)
            date_to = rec.date_to.replace(year=today.year)
            allocation = self.env['hr.leave.allocation'].create({
                'name': 'Carry Forward From %s' % rec.date_from.year,
                'employee_id': rec.employee_id.id,
                'holiday_status_id': rec.holiday_status_id.id,
                'number_of_days': number_of_days,
                'allocation_type': 'regular',
                'date_from': date_from,
                'date_to': date_to,
                'is_carry_forward': True,
            })
            allocation.action_confirm()
            allocation.action_validate()
            rec.write({'transferred': True})

    def _process_accrual_plan_level(self, level, start_period, start_date, end_period, end_date):

        res = super(HrLeaveAllocation, self)._process_accrual_plan_level(level, start_period, start_date, end_period, end_date)
        month_days = self.employee_company_id.days_per_year/12
        if level.frequency == 'daily':
            today = start_period
            last_day = (today.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            if today == last_day and last_day.day < month_days:
                res += (month_days - last_day.day) * res
            elif today == last_day and last_day.day > month_days:
                res = 0.0

        return res

    def _process_accrual_plans(self):
        """
        This method is part of the cron's process.
        The goal of this method is to retroactively apply accrual plan levels and progress from nextcall to today
        """
        today = fields.Date.today()
        first_allocation = _(
            """This allocation have already ran once, any modification won't be effective to the days allocated to the employee. If you need to change the configuration of the allocation, cancel and create a new one.""")
        for allocation in self:
            level_ids = allocation.accrual_plan_id.level_ids.sorted('sequence')
            if not level_ids:
                continue
            if not allocation.nextcall:
                first_level = level_ids[0]
                first_level_start_date = allocation.date_from + get_timedelta(first_level.start_count,
                                                                              first_level.start_type)
                if today < first_level_start_date:
                    # Accrual plan is not configured properly or has not started
                    continue
                allocation.lastcall = max(allocation.lastcall, first_level_start_date)
                allocation.nextcall = first_level._get_next_date(allocation.lastcall)
                if len(level_ids) > 1:
                    second_level_start_date = allocation.date_from + get_timedelta(level_ids[1].start_count,
                                                                                   level_ids[1].start_type)
                    allocation.nextcall = min(second_level_start_date, allocation.nextcall)
                allocation._message_log(body=first_allocation)
            days_added_per_level = defaultdict(lambda: 0)
            while allocation.nextcall <= today:
                (current_level, current_level_idx) = allocation._get_current_accrual_plan_level_id(allocation.nextcall)
                nextcall = current_level._get_next_date(allocation.nextcall)
                # Since _get_previous_date returns the given date if it corresponds to a call date
                # this will always return lastcall except possibly on the first call
                # this is used to prorate the first number of days given to the employee
                period_start = current_level._get_previous_date(allocation.lastcall)
                period_end = current_level._get_next_date(allocation.lastcall)
                # Also prorate this accrual in the event that we are passing from one level to another
                if current_level_idx < (
                        len(level_ids) - 1) and allocation.accrual_plan_id.transition_mode == 'immediately':
                    next_level = level_ids[current_level_idx + 1]
                    current_level_last_date = allocation.date_from + get_timedelta(next_level.start_count,
                                                                                   next_level.start_type)
                    if allocation.nextcall != current_level_last_date:
                        nextcall = min(nextcall, current_level_last_date)
                days_added_per_level[current_level] += allocation._process_accrual_plan_level(
                    current_level, period_start, allocation.lastcall, period_end, allocation.nextcall)
                if current_level.maximum_leave > 0 and sum(days_added_per_level.values()) > current_level.maximum_leave \
                        and allocation.lastcall.month == 12:
                    days_added_per_level[current_level] -= sum(
                        days_added_per_level.values()) - current_level.maximum_leave
                allocation.lastcall = allocation.nextcall
                allocation.nextcall = nextcall
            if days_added_per_level:
                number_of_days_to_add = allocation.number_of_days + sum(days_added_per_level.values())
                # Let's assume the limit of the last level is the correct one
                allocation.number_of_days = number_of_days_to_add
