# -*- coding: utf-8 -*-

from odoo import fields, models, tools, _
from datetime import timedelta, datetime


class HrLeaveBalance(models.Model):
    _name = 'hr.leave.balance'
    _description = 'Leave Balance'
    _auto = False
    _rec_name = 'leave_type'

    leave_type = fields.Many2one('hr.leave.type', string='leave Type')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    current_balance = fields.Float(string='Current Year Balance', compute='compute_employee_balance')
    accrued_balance = fields.Float(string='Accrued Balance')
    carry_forward_balance = fields.Float(string='Carry Forward Balance', compute='compute_employee_balance')
    total_balance = fields.Float(string='Total Balance', compute='compute_employee_balance')
    remaining_balance = fields.Float(string='Remaining Balance', default=0.0)
    leaves_taken = fields.Float(string='Leaves Taken', default=0.0)
    company_id = fields.Many2one('res.company', 'Company', related="employee_id.company_id")

    # balance_line_ids = fields.One2many('hr.leave.balance.line', string='Balance Lines',
    #                                    compute='compute_employee_balance')

    def compute_employee_balance(self):
        for record in self:
            record.total_balance = record.current_balance + record.carry_forward_balance
            # rec.remaining_balance = rec.accrued_balance - rec.leaves_taken
            if record.employee_id and self._context.get('to_date'):
                allocations = self.env['hr.leave.allocation'].search([('employee_id', '=', record.employee_id.id),
                                                                      ('state', '=', 'validate')])
                balance = sum([rec.number_of_days - rec.leaves_taken for rec in allocations])
                days = 0
                sign = 1
                accrual_allocations = allocations.filtered(lambda al: al.allocation_type == 'accrual')
                to_date = datetime.strptime(self._context.get('to_date'), "%Y-%m-%d").date()
                if accrual_allocations and to_date:
                    current_level = allocations[0]._get_current_accrual_plan_level_id(to_date)
                    nextcall = allocations[0].date_from
                    if allocations[0].nextcall:
                        nextcall = allocations[0].nextcall
                    date_from = nextcall - timedelta(days=1)
                    date_to = to_date
                    delta = date_to - date_from
                    if date_from > date_to:
                        date_from = to_date
                        sign = -1
                    z = 0
                    for i in range(abs(delta.days)):
                        end_date = date_from + timedelta(days=i)
                        days += allocations[0]._process_accrual_plan_level(current_level[0], date_from, date_from,
                                                                           end_date, end_date)
                        z += 1
                        days = days
                record.current_balance = balance + (days * sign)

    def init(self):
        tools.drop_view_if_exists(self._cr, 'hr_leave_balance')
        query = """
                        CREATE or REPLACE VIEW hr_leave_balance AS (
                        SELECT
                            min(e.id) as id,
                            e.id AS employee_id,
                            lt.id AS leave_type,
                            SUM(CASE WHEN a.state = 'validate' THEN a.number_of_days ELSE 0 END) AS accrued_balance,
                            (
                             SELECT SUM(CASE WHEN l.state = 'validate' THEN l.number_of_days ELSE 0 END) from hr_leave l
                             where l.holiday_status_id  = lt.id and l.employee_id = e.id
                            ) AS leaves_taken,
                             SUM(CASE WHEN a.state = 'validate' THEN a.number_of_days ELSE 0 END)
                             - (
                             SELECT SUM(CASE WHEN ll.state = 'validate' THEN ll.number_of_days ELSE 0 END)
                              from hr_leave ll
                             where ll.holiday_status_id  = lt.id and ll.employee_id = e.id
                            ) AS remaining_balance
                            FROM
                                hr_leave_allocation a
                            JOIN
                                hr_employee e ON e.id = a.employee_id
                            JOIN
                                hr_leave_type lt ON lt.id = a.holiday_status_id
                            GROUP BY
                                e.id,
                                e.name,
                                lt.id
                            ORDER BY
                                e.id,
                                lt.name
                            );
                        """
        self.env.cr.execute(query)

    def _get_leave_ids(self):
        employee = self.env['hr.employee'].browse(self.env.context.get('employee_id'))
        type_ids = []
        leave_types = self.env['hr.leave.type'].sudo().search(
            ['|', ('company_id', '=', False), ('company_id', '=', employee.company_id.id)])
        if employee:
            type_ids = []
            if employee and employee.gender:
                leave_types = leave_types.filtered(lambda line: line.gender_specific == 'all' or
                                                                line.gender_specific in employee.gender)
            if employee and employee.religion_id:
                leave_types = leave_types.filtered(lambda line: not line.religion_specific or
                                                                employee.religion_id in line.religions.ids)
            type_ids += leave_types and leave_types.ids
        return type_ids


# class HrLeaveBalanceLine(models.Model):
#     _name = 'hr.leave.balance.line'
#     _description = 'leave Balance lines'
#     _auto = False
#
#     allocation_id = fields.Many2one('hr.leave.allocation', string='Name')
#     balance = fields.Float(string='Balance', compute='_compute_balance')
#     leaves_taken = fields.Float(string='Leaves Taken', compute='_compute_balance')
#     remaining_balance = fields.Float(string='Remaining Balance', compute='_compute_balance')
#     employee_id = fields.Many2one('hr.employee', string='Employee')
#     leave_type_id = fields.Many2one('hr.leave.type', string='leave Type')
#     is_carry_forward = fields.Boolean(string='Is Carry Forward?')
#
#     @api.depends('allocation_id')
#     def _compute_balance(self):
#         for line in self:
#             line.leaves_taken = line.allocation_id.leaves_taken
#             line.balance = line.allocation_id.number_of_days_display
#             line.remaining_balance = line.balance - line.leaves_taken
#
#     def init(self):
#         tools.drop_view_if_exists(self._cr, 'hr_leave_balance_line')
#         query = """
#                 CREATE or REPLACE VIEW hr_leave_balance_line AS (
#                 SELECT
#                     MIN(id) as id,
#                     id as allocation_id,
#                     employee_id as employee_id,
#                     holiday_status_id as leave_type_id,
#                     is_carry_forward as is_carry_forward
#                 FROM
#                     hr_leave_allocation
#                 WHERE state='validate'
#                 GROUP BY allocation_id
#                 );
#                 """
#         self.env.cr.execute(query)
