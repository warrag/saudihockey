# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)
grey = "\x1b[38;21m"
yellow = "\x1b[33;21m"
red = "\x1b[31;21m"
bold_red = "\x1b[31;1m"
reset = "\x1b[0m"
green = "\x1b[32m"
blue = "\x1b[34m"


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    last_allocation_date = fields.Date()
    allocation_ids = fields.One2many('hr.leave.allocation', 'employee_id')

    def get_employee_allocation(self, employee):
        employee = employee
        _logger.info(blue)
        _logger.info('employee ' + str(employee) + reset)
        _logger.info(yellow)
        _logger.info('employee.join_date ' + str(employee.join_date) + reset)

        company = self.env['res.company'].search([('id', '=', self.env.user.company_id.id)])
        allocation_obj = self.env['hr.leave.allocation']
        no_of_days_per_year = company.days_per_year
        leave_type_id = company.leave_type_id
        leave_id = company.leave_id
        unpaid_type = company.unpaid_type
        first_period = company.first_period
        deserve_first_period = company.deserve_first_period
        deserve_second_period = company.deserve_second_period
        leave_ids = self.env['hr.leave']
        if employee.join_date:
            leave = 0.0
            total_days = (fields.date.today() - employee.join_date).days
            leave_obj_id = leave_ids.search([('employee_id', '=', employee.id),
                                             ('holiday_status_id', '=', leave_id.id)])
            if leave_obj_id:
                for l in leave_obj_id:
                    leave += l.number_of_days

            if unpaid_type == 'Add':
                total_work_days = total_days - leave
            else:
                total_work_days = total_days
            no_of_years = total_work_days / no_of_days_per_year
            if no_of_years <= first_period:  # less than 5 years
                no_of_deserved_days = (fields.date.today() - employee.join_date).days
                no_of_years_deserved = no_of_deserved_days / no_of_days_per_year  # 1.3 year
                deserve_period = no_of_years_deserved * deserve_first_period

            else: # no_of_years > first_period   this is number of years from joining date
                no_of_deserved_days = (fields.date.today() - employee.join_date).days
                no_of_years_deserved = no_of_deserved_days / no_of_days_per_year  # 1.3 year
                period_after_5_years = no_of_years - first_period  # No of period after 5 years .3 month
                period_before_5_years = no_of_years_deserved - period_after_5_years  # No of period before 5 years 1 year


                if period_before_5_years <= 0:  # get allocation with 30 days
                    deserve_period = no_of_years_deserved * deserve_second_period

                else:  # get allocation with 30 days and 21 days
                    deserved_before_5_years = period_before_5_years * deserve_first_period
                    deserved_after_5_years= period_after_5_years * deserve_second_period
                    deserve_period=deserved_before_5_years+deserved_after_5_years

            final_period = deserve_period

            a = allocation_obj.create({
                'name': 'Annual Allocation',
                'holiday_status_id': leave_type_id.id,
                'number_of_days': final_period,
                'employee_id': employee.id,
                'last_allocation_date': fields.Date.today(),
                'allocated_until': fields.Date.today(),
            })
            employee.last_allocation_date = fields.Date.today()
            print(a.id)

    @api.model
    def cron_employee_annual_allocation(self):

        _logger.info(blue)
        _logger.info('cron_employee_annual_allocation ' + reset)
        company = self.env['res.company'].search([('id', '=', self.env.user.company_id.id)])
        no_of_days_per_year = company.days_per_year
        allocation_type = company.allocation_type
        employee_ids = self.env['hr.employee'].search([])
        contract_obj = self.env['hr.contract']
        _logger.info(yellow)
        _logger.info('employee_ids ' + str(employee_ids) + reset)
        for employee in employee_ids:
            contract_id = contract_obj.search([('employee_id', '=', employee.id),
                                               ('state', '=', 'open')])
            if contract_id:
                _logger.info('contract_id ' + str(contract_id) + reset)
                if employee.last_allocation_date:
                    _logger.info(blue)
                    _logger.info('employee.last_allocation_date '+ str(employee.last_allocation_date) + reset)
                    allocation_per_days = (fields.date.today() - employee.last_allocation_date).days
                    allocation_per_year = allocation_per_days / no_of_days_per_year
                    allocation_per_month = allocation_per_year / 12
                    if allocation_type == 'Yearly':
                        if allocation_per_year >= 1:
                            self.get_employee_allocation(employee)
                    elif allocation_type == 'Monthly':
                        if allocation_per_month >= 1:
                            self.get_employee_allocation(employee)
                    elif allocation_type == 'Daily':
                        if allocation_per_days >= 1:
                            self.get_employee_allocation(employee)
                else:
                    self.get_employee_allocation(employee)


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    last_allocation_date = fields.Date()
