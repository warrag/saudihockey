from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    is_annual_leave = fields.Boolean(string='Is Annual Leave?')
    carry_forward = fields.Boolean(string='Carry Forward', help="Carry forward to next year")
    max_carry_balance = fields.Float(string='Maximum Carry Balance', help="Carry forward leave balance to next year")
    calculation_type = fields.Selection([('working_days', 'Working Days'), ('calendar_days', 'Calendar Days')],
                                        string='Leave Calculation Type')
    salary_payment = fields.Selection([('paid', 'Paid'), ('unpaid', 'Unpaid')], default='paid')
    gender_specific = fields.Selection([('all', "All Genders"), ('male', 'Male'), ('female', 'Female')], default='all')
    religion_specific = fields.Boolean(string='For specific religion')
    religions = fields.Many2many('employee.religion')

    plus_type = fields.Selection(string='Type', selection=[
        ('permission', 'Permission'),
        ('leave', 'Leave'), ], required=True, default='leave')
    max_negative_days = fields.Float("Maximum Negative Days", default=30)

    # multi_level_validation = fields.Boolean(
    #     string='Multiple Level Approval',
    #     help="If checked then multi-level approval is necessary")
    # leave_validation_type = fields.Selection(
    #     selection_add=[('multi', 'Multi Level Approval')])
    # leave_approval_ids = fields.One2many('hr.holidays.approvals',
    #                                      'leave_type_id',
    #                                      string='Leave Approvals',
    #                                      help="Leave validators")
    allow_credit = fields.Boolean(string='Allow Credit',
                                  help=(
                                      'If set to true, employees would be able to make requests for this'
                                      ' leave type even if allocated amount is insufficient.'
                                  ),
                                  )
    creditable_employee_ids = fields.Many2many(
        string='Creditable Employees',
        comodel_name='hr.employee',
        help='If set, limits credit allowance to specified employees',
    )
    creditable_employee_category_ids = fields.Many2many(
        string='Creditable Employee Tags',
        comodel_name='hr.employee.category',
        help=(
            'If set, limits credit allowance to employees with at least one of'
            ' specified tags'
        ),
    )
    creditable_department_ids = fields.Many2many(
        string='Creditable Departments',
        comodel_name='hr.department',
        help=(
            'If set, limits credit allowance to employees of specified'
            ' departments'
        ),
    )
    max_yearly_leaves = fields.Float(string='Maximum Allowed')

    # @api.onchange('leave_validation_type')
    # def enable_multi_level_validation(self):
    #     """ Enabling the boolean field of multilevel validation"""
    #     self.multi_level_validation = True if (
    #             self.leave_validation_type == 'multi') else False

    @api.constrains('is_annual_leave')
    def _check_(self):
        checked_bool = self.search([('id', '!=', self.id), ('is_annual_leave', '=', True)], limit=1)
        if self.is_annual_leave and checked_bool:
            raise ValidationError(_("There's already one annual leave defined with name: '%s'") % checked_bool.name)

    # def unlink(self):
    #     leave_type_id = self.env.user.company_id.leave_type_id
    #     for record in self:
    #         if leave_type_id.id == record.id:
    #             raise UserError(_("You are not allowed to delete This record!!"))
    #     return super(HrLeaveType, self).unlink()

    def name_get(self):
        if not self._context.get('is_balance'):
            return super(HrLeaveType, self).name_get()
        res = []
        for record in self:
            name = record.name
            res.append((record.id, name))
        return res


class HrLeaveValidators(models.Model):
    """ Model for leave validators in Leave Types configuration """
    _name = 'hr.holidays.approvals'

    leave_type_id = fields.Many2one('hr.leave.type')

    holiday_approval_ids = fields.Many2one('res.users',
                                           string='Leave Approvals',
                                           help="Leave Approvals",
                                           domain="[('share','=',False)]")


class LeaveValidationStatus(models.Model):
    """ Model for leave validators and their status for each leave request """
    _name = 'leave.approval.status'

    holiday_status = fields.Many2one('hr.leave')

    approval_users = fields.Many2one('res.users', string='Leave Approvals',
                                     help="Leave Approvals",
                                     domain="[('share','=',False)]")
    approval_status = fields.Boolean(string='Approve Status', readonly=True,
                                     default=False,
                                     track_visibility='always', help="Status")
    leave_comments = fields.Text(string='Comments', help="Comments")

    @api.onchange('approval_users')
    def prevent_change(self):
        """ Prevent Changing leave validators from leave request form """
        raise UserError(_(
            "Changing leave approval is not permitted. You can only change "
            "it from Leave Types Configuration"))
