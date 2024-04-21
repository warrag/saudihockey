# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import date, timedelta
from odoo.addons.hr_holidays.models.hr_leave import HolidaysRequest
from collections import defaultdict
from pytz import timezone, UTC
from pytz import utc
from odoo.osv import expression


def datetime_to_string(dt):
    """ Convert the given datetime (converted in UTC) to a string value. """
    return fields.Datetime.to_string(dt.astimezone(utc))


def string_to_datetime(value):
    """ Convert the given string value to a datetime in UTC. """
    return utc.localize(fields.Datetime.from_string(value))


def timezone_datetime(time):
    if not time.tzinfo:
        time = time.replace(tzinfo=utc)
    return time


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    def _default_holiday_status_id(self):

        domain = []
        if 'default_plus_type' in self._context:
            if self._context.get('default_plus_type') == 'leave':
                domain.append(('plus_type', '=', 'leave'))
            else:
                domain.append(('plus_type', '=', 'permission'))
        else:
            domain.append(('plus_type', '=', 'leave'))
        return self.env['hr.leave.type'].search(domain, limit=1)

    def _domain_holiday_status_id(self):

        domain = ['|', '|', ('allow_credit', '=', True), ('requires_allocation', '=', 'no'),
                  ('has_valid_allocation', '=', True)]

        if self._context.get('default_plus_type') == 'leave':
            domain.append(('plus_type', '=', 'leave'))
        else:
            domain.append(('plus_type', '=', 'permission'))

        return domain

    plus_type = fields.Selection(string='Type', selection=[
        ('permission', 'Permission'),
        ('leave', 'Leave'), ], required=True, default='leave')
    holiday_status_id = fields.Many2one(
        "hr.leave.type", compute='_compute_from_employee_id', store=True, string="Time Off Type", required=True,
        readonly=False,
        states={'cancel': [('readonly', True)], 'refuse': [('readonly', True)], 'validate1': [('readonly', True)],
                'validate': [('readonly', True)]},
        domain=_domain_holiday_status_id,
        default=_default_holiday_status_id)
    duration_hours = fields.Char(compute='_compute_duration_hours')
    refuse_reason = fields.Text('Refuse Reason', readonly=True)
    show_cut_button = fields.Boolean(string='show cut button', compute='_compute_show_cut')
    cut_done = fields.Boolean()
    can_refuse = fields.Boolean(compute='compute_is_responsible')

    @api.depends('holiday_status_id', 'state', 'holiday_status_id.responsible_id')
    def compute_is_responsible(self):
        for record in self:
            if record.holiday_status_id.responsible_id.id == self.env.user.id or record.state != 'validate':
                record.can_refuse = True
            else:
                record.can_refuse = False

    def _compute_show_cut(self):
        for record in self:
            today = date.today()
            if record.state == 'validate' and today >= record.request_date_from and today <= record.request_date_to and record.holiday_status_id.request_unit == 'day':
                record.show_cut_button = True
            else:
                record.show_cut_button = False

    @api.depends('number_of_hours_display', 'request_date_from', 'date_from', 'date_to')
    def _compute_duration_hours(self):
        for record in self:
            hours_display = '00:00'
            if record.request_unit_hours:
                hours_display = '{0:02.0f}:{1:02.0f}'.format(*divmod(record.number_of_hours_display * 60, 60))
            record.duration_hours = hours_display

    def _compute_duration_display(self):
        res = super(HrLeave, self)._compute_duration_display()
        for leave in self:
            if leave.leave_type_request_unit == 'hour':
                leave.duration_display = leave.duration_hours + ' Hours'

        return res

    @api.constrains('supported_attachment_ids')
    def _check_support_document(self):
        for record in self:
            if record.holiday_status_id.support_document and not record.supported_attachment_ids:
                raise ValidationError(_('Please attach supporting documents'))

    @api.constrains('holiday_status_id')
    def eligibility_check(self):
        for record in self:
            if record.holiday_status_id.gender_specific != 'all' and \
                    record.holiday_status_id.gender_specific != record.employee_id.gender:
                raise ValidationError(_('You are not eligible to apply this leave\n please contact time off officer'))
            if record.holiday_status_id.religion_specific and record.employee_id.religion_id.id not in \
                    record.holiday_status_id.religions.ids:
                raise ValidationError(_('You are not eligible to apply this leave\n please contact time off officer'))

    def action_validate(self):
        res = super(HrLeave, self).action_validate()
        for record in self:
            contract_id = self.env['hr.contract'].search([('employee_id', '=', record.employee_id.id),
                                                          ('state', '=', 'open'),
                                                          ])
            if contract_id and self.holiday_status_id.unpaid:
                contract_id.state = 'partial'

        return res

    # @api.model
    # def create(self, values):
    #     print(values)
    #     res = super(HrLeave, self).create(values)
    #     for rec in self:
    #         allocation_id = self.env['hr.leave.allocation'].search([('employee_id', '=', values['employee_id']),
    #                                                                 ('state', '=', 'validate')
    #                                                                 ], order='id desc', limit=1)
    #         if allocation_id:
    #             if allocation_id.available_from:
    #                 request_date_from = datetime.strptime(values['request_date_from'], '%Y-%m-%d')
    #                 date_from = request_date_from.date()
    #                 if date_from < allocation_id.available_from or \
    #                         date_from > allocation_id.expiry_date:
    #                     raise UserError(_("You Aren't Allowed To Make This Leave "
    #                                     "You Can Make Between %s and %s"
    #                                     % (allocation_id.available_from, allocation_id.expiry_date)))
    #     return res

    @api.depends('date_from', 'date_to', 'employee_id')
    def _compute_number_of_days(self):
        for holiday in self:
            if holiday.date_from and holiday.date_to:
                global_leave = self._get_global_leaves(holiday.date_from, holiday.date_to,
                                                       holiday.employee_id.resource_id,
                                                       holiday.employee_id.resource_calendar_id)
                number_of_days = \
                    holiday._get_number_of_days(holiday.date_from, holiday.date_to, holiday.employee_id.id)['days']
                if self.holiday_status_id.calculation_type == 'calendar_days':
                    all_days = (holiday.date_to - holiday.date_from).days + 1
                    number_of_days = abs(all_days - global_leave)
                elif self.holiday_status_id.calculation_type == 'working_days':
                    number_of_days = number_of_days
                holiday.number_of_days = number_of_days
            else:
                holiday.number_of_days = 0

    def _get_global_leaves(self, date_from, date_to, resource, calendar_id):
        leave_date_from = date_from
        datetime_from = timezone_datetime(date_from)
        datetime_to = timezone_datetime(date_to)
        resource_ids = [resource.id, False] if resource else [False]
        domain = [
            ('calendar_id', '=', calendar_id.id),
            ('resource_id', 'in', resource_ids),
            ('date_from', '<=', datetime_to_string(datetime_to)),
            ('date_to', '>=', datetime_to_string(datetime_from)),
        ]

        all_period_date = []
        number_of_day = 0
        delta = datetime_to - datetime_from
        for i in range(delta.days + 1):
            day = leave_date_from + timedelta(days=i)
            all_period_date.append(day)
        for leave in self.env['resource.calendar.leaves'].search(domain):
            global_period = []
            delta = leave.date_to - leave.date_from
            for i in range(delta.days + 1):
                day = leave_date_from + timedelta(days=i)
                global_period.append(day)
            for date in all_period_date:
                if date in global_period:
                    number_of_day += 1
        return number_of_day

    def _get_weekend_days(self, date_from, date_to, employee_id):
        working_days = employee_id.resource_calendar_id.attendance_ids.mapped('dayofweek')
        all_days = [str((date_from + timedelta(x + 1)).weekday()) for x in range((date_to - date_from).days)]
        all_days.insert(0, str(date_from.weekday()))
        weekend_days = sum(1 for day in all_days if day not in working_days)
        return weekend_days

    def _check_holidays(self):
        not_creditable_requests = self.filtered(
            lambda holiday: not holiday._is_holiday_credit_allowed()
        )
        return super(HrLeave, not_creditable_requests)._check_holidays()

    def _check_allocation_duration(self):
        not_creditable_requests = self.filtered(
            lambda holiday: not holiday._is_holiday_credit_allowed()
        )
        return super(HrLeave, not_creditable_requests)._check_allocation_duration()

    def _is_holiday_credit_allowed(self):
        self.ensure_one()
        if self.employee_id and self.date_from and self.date_to and not self.env.context.get('default_plus_type'):
            self._check_balance()
        leave_type = self.holiday_status_id

        if not leave_type.allow_credit:
            return False

        if self.employee_id in leave_type.creditable_employee_ids:
            return True

        if self.employee_id in (
                leave_type.creditable_employee_category_ids.mapped(
                    'employee_ids'
                )):
            return True

        if self.employee_id in (
                leave_type.creditable_department_ids.mapped(
                    'member_ids'
                )):
            return True

        return not leave_type.creditable_employee_ids and \
               not leave_type.creditable_employee_category_ids and \
               not leave_type.creditable_department_ids

    def _check_balance(self):
        for leave in self:
            taken_leave_number = 0
            available_balance = 0
            cary_forward_balance = 0
            allocations = self.env['hr.leave.allocation'].search_read(
                [
                    ('holiday_status_id', 'in', self.holiday_status_id.ids),
                    ('employee_id', 'in', self.employee_id.ids),
                    ('state', '=', 'validate'),
                    ('date_from', '<=', max(self.mapped('date_from'))),
                ], ['id', 'date_from', 'date_to', 'holiday_status_id',
                    'employee_id', 'max_leaves', 'taken_leave_ids', 'is_carry_forward'],
                order="date_to, id"
            )
            allocations_dict = defaultdict(lambda: [])
            for allocation in allocations:
                allocation['taken_leaves'] = self.env['hr.leave'].browse(allocation.pop('taken_leave_ids')) \
                    .filtered(lambda leave: leave.state in ['confirm', 'validate', 'validate1'])
                allocations_dict[(allocation['holiday_status_id'][0], allocation['employee_id'][0])].append(allocation)
            date_to = leave.date_to.replace(tzinfo=UTC).astimezone(timezone(leave.tz)).date()
            date_from = leave.date_from.replace(tzinfo=UTC).astimezone(timezone(leave.tz)).date()
            leave_unit = 'number_of_%s_display' % ('hours' if leave.leave_type_request_unit == 'hour' else 'days')
            for allocation in allocations_dict[(leave.holiday_status_id.id, leave.employee_id.id)]:
                date_to_check = allocation['date_to'] >= date_to if allocation['date_to'] else True
                date_from_check = allocation['date_from'] <= date_from
                if (date_to_check and date_from_check):
                    available_balance += allocation['max_leaves']
                    if allocation['is_carry_forward']:
                        cary_forward_balance += allocation['max_leaves']
                    allocation_taken_leaves = allocation['taken_leaves'] - leave
                    taken_leave_number = sum(allocation_taken_leaves.mapped(leave_unit))
                    available_balance -= taken_leave_number
            # available_balance = available_balance+leave.employee_id.contract_id.annual_leave_balance + cary_forward_balance - taken_leave_number
            max_negative_days = leave.holiday_status_id.max_negative_days if leave.holiday_status_id.max_negative_days > 0 else leave.employee_id.contract_id.annual_leave_balance
            available_balance = available_balance + max_negative_days + cary_forward_balance
            if leave.number_of_days:
                taken_leave_number += leave.number_of_days
            if leave.holiday_status_id.allow_credit:
                if leave.number_of_days > available_balance:
                    raise ValidationError(_("Your yearly leave balance has been exceeded\n."))

    @api.depends('holiday_status_id.requires_allocation', 'validation_type', 'employee_id', 'date_from', 'date_to')
    def _compute_from_holiday_status_id(self):
        uncreditable_requests = self.filtered(
            lambda holiday: not holiday._is_holiday_credit_allowed())
        invalid_self = self.filtered(lambda leave: not leave.date_to or not leave.date_from)
        if invalid_self:
            invalid_self.update({'holiday_allocation_id': False})
            self = self - invalid_self
        if not self:
            return
        allocations = self.env['hr.leave.allocation'].search_read(
            [
                ('holiday_status_id', 'in', self.holiday_status_id.ids),
                ('employee_id', 'in', self.employee_id.ids),
                ('state', '=', 'validate'),
                '|',
                ('date_to', '>=', min(self.mapped('date_to'))),
                '&',
                ('date_to', '=', False),
                ('date_from', '<=', max(self.mapped('date_from'))),
            ], ['id', 'date_from', 'date_to', 'holiday_status_id', 'employee_id', 'max_leaves', 'taken_leave_ids'],
            order="date_to, id"
        )
        allocations_dict = defaultdict(lambda: [])
        for allocation in allocations:
            allocation['taken_leaves'] = self.env['hr.leave'].browse(allocation.pop('taken_leave_ids')) \
                .filtered(lambda leave: leave.state in ['confirm', 'validate', 'validate1'])
            allocations_dict[(allocation['holiday_status_id'][0], allocation['employee_id'][0])].append(allocation)

        for leave in self:
            if leave.holiday_status_id.requires_allocation == 'yes' and leave.date_from and leave.date_to:
                found_allocation = False
                date_to = leave.date_to.replace(tzinfo=UTC).astimezone(timezone(leave.tz)).date()
                date_from = leave.date_from.replace(tzinfo=UTC).astimezone(timezone(leave.tz)).date()
                leave_unit = 'number_of_%s_display' % ('hours' if leave.leave_type_request_unit == 'hour' else 'days')
                for allocation in allocations_dict[(leave.holiday_status_id.id, leave.employee_id.id)]:
                    date_to_check = allocation['date_to'] >= date_to if allocation['date_to'] else True
                    date_from_check = allocation['date_from'] <= date_from
                    if (date_to_check and date_from_check):
                        allocation_taken_leaves = allocation['taken_leaves'] - leave
                        allocation_taken_number_of_units = sum(allocation_taken_leaves.mapped(leave_unit))
                        leave_number_of_units = leave[leave_unit]
                        if allocation['max_leaves'] >= allocation_taken_number_of_units + leave_number_of_units:
                            found_allocation = allocation['id']
                            break
                        elif not uncreditable_requests:
                            found_allocation = allocation['id']

                leave.holiday_allocation_id = self.env['hr.leave.allocation'].browse(
                    found_allocation) if found_allocation else False
            else:
                leave.holiday_allocation_id = False

    HolidaysRequest._compute_from_holiday_status_id = _compute_from_holiday_status_id

    def _validate_leave_request(self):
        """ Validate time off requests (holiday_type='employee')
        by creating a calendar event and a resource time off. """
        holidays = self.filtered(lambda request: request.holiday_type == 'employee' and request.employee_id)
        holidays._create_resource_leave()
        meeting_holidays = holidays.filtered(lambda l: l.holiday_status_id.create_calendar_meeting)
        meetings = self.env['calendar.event']
        if meeting_holidays:
            meeting_values_for_user_id = meeting_holidays._prepare_holidays_meeting_values()
            Meeting = self.env['calendar.event']
            for user_id, meeting_values in meeting_values_for_user_id.items():
                meetings += Meeting.with_user(user_id or self.env.uid).with_context(
                    no_mail_to_attendees=True,
                    calendar_no_videocall=True,
                    active_model=self._name
                ).sudo().create(meeting_values)
        Holiday = self.env['hr.leave']
        for meeting in meetings:
            Holiday.browse(meeting.res_id).meeting_id = meeting

    HolidaysRequest._validate_leave_request = _validate_leave_request

    def _get_current_balance(self):
        allocations = self.env['hr.leave.allocation'].search([('holiday_status_id', '=', self.holiday_status_id.id),
                                                              ('state', '=', 'validate'),
                                                              ('employee_id', '=', self.employee_id.id)])
        taken_leaves = self.search([('holiday_status_id', '=', self.holiday_status_id.id),
                                    ('employee_id', '=', self.employee_id.id), ('state', '=', 'validate'),
                                   ('id', '!=', self.id)])
        accrued_balance = sum([allocation.number_of_days for allocation in allocations])
        taken_leaves_balance = sum([leave.number_of_days for leave in taken_leaves])
        remaining_balance = round(accrued_balance + taken_leaves_balance, 2)
        return remaining_balance


class SickLeaves(models.Model):
    _name = 'sick.leave.configuration'
    _description = 'Sick Leaves'

    leave_type = fields.Many2one('hr.leave.type', string='Sick Leave', required=True)
    name = fields.Char(string='Name', required=True, translated=True)
    active = fields.Boolean(string='Active')
    rule_ids = fields.One2many('sick.leave.rule', 'sick_leave_config_id')
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)


class StickLeaveRules(models.Model):
    _name = 'sick.leave.rule'
    _description = 'Sick Leave rules'

    name = fields.Char(string='Description', required=True, translated=True)
    days = fields.Integer(string='Days', required=True)
    deduction = fields.Float(string='Deduction Percentage', required=True)
    sick_leave_config_id = fields.Many2one('sick.leave.configuration')
