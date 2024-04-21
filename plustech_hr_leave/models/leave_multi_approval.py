# -*- coding: utf-8 -*-

from odoo import models, api, fields, _
from odoo.exceptions import UserError


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    leave_approvals = fields.One2many('leave.validation.status',
                                      'holiday_status',
                                      string='Leave Validators',
                                      track_visibility='always',
                                      help="Leave approvals")
    multi_level_validation = fields.Boolean(
        string='Multiple Level Approval',
        related='holiday_status_id.multi_level_validation',
        help="If checked then multi-level approval is necessary")
    button_visibility = fields.Boolean(default=True,
                                       compute='_get_current_user_details',
                                       string='Multiple Level Approval')
    next_approval = fields.Boolean(compute='_compute_next_approval')
    next_approver_id = fields.Many2one('res.users')

    @api.depends('state', 'employee_id', 'department_id', 'next_approver_id')
    def _compute_can_approve(self):
        res = super(HrLeave, self)._compute_can_approve()
        for holiday in self:
            if holiday.validation_type:
                if holiday.next_approver_id == self.env.user:
                    holiday.can_approve = True
                else:
                    holiday.can_approve = False
        return res

    def _compute_next_approval(self):
        for holiday in self:
            current_user = holiday.leave_approvals.filtered(lambda line: line.validating_users == self.env.user)
            if current_user:
                current_user = current_user[0]
            required_approval_users = holiday.leave_approvals.filtered(
                lambda line: line.validating_users != self.env.user
                             and line.validation_status == False and line.sequence < current_user.sequence)
            required_users = required_approval_users.mapped('sequence')
            if len(required_users) == 0 or not holiday.multi_level_validation:
                holiday.next_approval = True
                next_approver_users = holiday.leave_approvals.filtered(
                    lambda line: not line.validation_status).mapped('validating_users')
                next_approver_id = next_approver_users[0].id if next_approver_users else False
                holiday.sudo().write({'next_approver_id': next_approver_id})
            else:
                holiday.next_approval = False

    def _get_responsible_for_approval(self):
        responsible = super(HrLeave, self)._get_responsible_for_approval()
        if self.validation_type == 'multi':
            approved_users = self.leave_approvals.filtered(lambda line: line.validation_status == True)
            if not approved_users:
                sequence = min(self.leave_approvals.mapped('sequence'))
                responsible = self.leave_approvals.filtered(lambda se: se.sequence == sequence).validating_users
            else:
                sequence = max(approved_users.mapped('sequence'))
                responsible = self.leave_approvals.filtered(lambda se: se.sequence == sequence + 1).validating_users
        return responsible

    def activity_update(self):
        multi_to_do = self.env['hr.leave']
        for holiday in self:
            activity_type = self.env.ref('hr_holidays.mail_act_leave_approval')
            domain = [
                ('res_model', '=', 'hr.leave'),
                ('res_id', 'in', holiday.ids),
                ('activity_type_id', '=', activity_type.id),
                ('user_id', '=', self.env.user.id)
            ]
            activities = self.env['mail.activity'].search(domain)
            if holiday.multi_level_validation and holiday.button_visibility and len(activities) >= 0:
                multi_to_do |= holiday
        if multi_to_do:
            multi_to_do.activity_feedback(
                ['hr_holidays.mail_act_leave_approval'])
        return super(HrLeave, self).activity_update()

    def action_approve(self):
        """ Check if any pending tasks is added if so reassign the pending
        task else call approval """
        # if leave_validation_type == 'both':
        # this method is the first approval
        # if leave_validation_type != 'both': t
        # his method calls action_validate() below
        if any(holiday.state != 'confirm' for holiday in self):
            raise UserError(_(
                'Leave request must be confirmed ("To Approve")'
                ' in order to approve it.'))
        return self.approval_check()

    def approval_check(self):
        """ Check all leave validators approved the leave request if approved
         change the current request stage to Approved"""

        current_employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)], limit=1)

        active_id = self.env.context.get('active_id') if self.env.context.get(
            'active_id') else self.id

        user = self.env['hr.leave'].search([('id', '=', active_id)], limit=1)
        for user_obj in user.leave_approvals.mapped(
                'validating_users').filtered(lambda l: l.id == self.env.uid):
            validation_obj = user.leave_approvals.search(
                [('holiday_status', '=', user.id),
                 ('validating_users', '=', self.env.uid)])
            validation_obj.validation_status = True
            validation_obj.validation_date = fields.Date.today()
        approval_flag = True
        for user_obj in user.leave_approvals:
            if not user_obj.validation_status:
                approval_flag = False
        if approval_flag:
            user.filtered(
                lambda hol: hol.validation_type == 'both').sudo().write(
                {'state': 'validate1',
                 'first_approver_id': current_employee.id})
            user.filtered(
                lambda hol:
                not hol.validation_type == 'both').sudo().action_validate()
            if not user.env.context.get('leave_fast_create'):
                user.activity_update()
            return True
        else:
            if not user.env.context.get('leave_fast_create'):
                user.activity_update()
            return False

    def action_refuse(self):
        """ Refuse the leave request if the current user is in
        validators list """
        current_employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)], limit=1)

        approval_access = False
        for user in self.leave_approvals:
            if user.validating_users.id == self.env.uid:
                approval_access = True
        if approval_access:
            for holiday in self:
                if holiday.state not in ['confirm', 'validate', 'validate1']:
                    raise UserError(_(
                        'Leave request must be confirmed '
                        'or validated in order to refuse it.'))

                if holiday.state == 'validate1':
                    holiday.sudo().write(
                        {'state': 'refuse',
                         'first_approver_id': current_employee.id})
                else:
                    holiday.sudo().write(
                        {'state': 'refuse',
                         'second_approver_id': current_employee.id})
                # Delete the meeting
                if holiday.meeting_id:
                    holiday.meeting_id.unlink()
                # If a category that created several holidays,
                # cancel all related
                holiday.linked_request_ids.action_refuse()
            self._remove_resource_leave()
            self.activity_update()
            validation_obj = self.leave_approvals.search(
                [('holiday_status', '=', self.id),
                 ('validating_users', '=', self.env.uid)])
            validation_obj.validation_status = False
            return True
        else:
            for holiday in self:
                if holiday.state not in ['confirm', 'validate', 'validate1']:
                    raise UserError(_(
                        'Leave request must be confirmed '
                        'or validated in order to refuse it.'))

                if holiday.state == 'validate1':
                    holiday.write({'state': 'refuse',
                                   'first_approver_id': current_employee.id})
                else:
                    holiday.write({'state': 'refuse',
                                   'second_approver_id': current_employee.id})
                # Delete the meeting
                if holiday.meeting_id:
                    holiday.meeting_id.unlink()
                # If a category that created several holidays,
                # cancel all related
                holiday.linked_request_ids.action_refuse()
            self._remove_resource_leave()
            self.activity_update()
            return True

    def action_draft(self):
        """ Reset all validation status to false when leave request
        set to draft stage"""
        for user in self.leave_approvals:
            user.validation_status = False
        return super(HrLeave, self).action_draft()

    @api.onchange('holiday_status_id', 'employee_id')
    def add_validators(self):
        """ Update the tree view and add new validators
        when leave type is changed in leave request form """
        li = []
        self.leave_approvals = [(5, 0, 0)]
        li2 = []
        for user in self.leave_approvals:
            li2.append(user.validating_users.id)
        for user in self.holiday_status_id.leave_validators.filtered(
                lambda l: l.holiday_validators.id not in li2):
            li.append((0, 0, {
                'validating_users': user.holiday_validators.id,
                'sequence': user.sequence
            }))
        if self.holiday_status_id.leave_validators:
            sequence = min(self.holiday_status_id.leave_validators.mapped('sequence'))
            li.append((0, 0, {
                'validating_users': self.employee_id.leave_manager_id.id,
                'sequence': sequence - 1
            }))
        self.leave_approvals = li

    @api.depends('holiday_status_id', 'request_date_from', 'state')
    def _get_current_user_details(self):
        for leave in self:
            type_leave = leave.holiday_status_id.leave_validation_type
            button_visibility = False
            if type_leave == 'multi':
                for val in leave.leave_approvals:
                    if val.validating_users.id == self.env.uid:
                        if val.validation_status:
                            button_visibility = True
                        else:
                            button_visibility = False

                    # else:
                    #     button_visibility = True
            leave.button_visibility = button_visibility


class HrLeaveTypes(models.Model):
    """ Extend model to add multilevel approval """
    _inherit = 'hr.leave.type'

    multi_level_validation = fields.Boolean(
        string='Multiple Level Approval',
        help="If checked then multi-level approval is necessary")
    leave_validation_type = fields.Selection(
        selection_add=[('multi', 'Multi Level Approval')])
    leave_validators = fields.One2many('hr.holidays.validators',
                                       'hr_holiday_status',
                                       string='Leave Validators',
                                       help="Leave validators", order='sequence')

    @api.onchange('leave_validation_type')
    def enable_multi_level_validation(self):
        """ Enabling the boolean field of multilevel validation"""
        self.multi_level_validation = True if (
                self.leave_validation_type == 'multi') else False

    @api.constrains('leave_validators')
    def check_leave_validators(self):
        for each in self:
            if not each.leave_validators \
                    and each.leave_validation_type == 'multi':
                raise UserError(_('You cannot make leave validators empty '
                                  'when selecting Multi Level Approval'))


class HrLeaveValidators(models.Model):
    """ Model for leave validators in Leave Types configuration """
    _name = 'hr.holidays.validators'
    _order = "sequence, id"

    hr_holiday_status = fields.Many2one('hr.leave.type')

    holiday_validators = fields.Many2one('res.users',
                                         string='Leave Validators',
                                         help="Leave validators",
                                         domain="[('share','=',False)]")
    sequence = fields.Integer(default=10, help="Gives the sequence order when "
                                               "displaying a list of validators.")


class LeaveValidationStatus(models.Model):
    """ Model for leave validators and their status for each leave request """
    _name = 'leave.validation.status'
    _order = 'sequence'

    holiday_status = fields.Many2one('hr.leave')

    validating_users = fields.Many2one('res.users', string='Leave Validators',
                                       help="Leave validators",
                                       domain="[('share','=',False)]")
    validation_status = fields.Boolean(string='Approve Status', readonly=True,
                                       default=False,
                                       track_visibility='always', help="Status")
    leave_comments = fields.Text(string='Comments', help="Comments")
    sequence = fields.Integer()
    validation_date = fields.Date()

    @api.onchange('validating_users')
    def prevent_change(self):
        """ Prevent Changing leave validators from leave request form """
        raise UserError(_(
            "Changing leave validators is not permitted. You can only change "
            "it from Leave Types Configuration"))
