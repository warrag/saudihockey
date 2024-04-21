# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError
from odoo import models, fields, api, _


class HrEmployeeShift(models.Model):
    _name = 'hr.employee.shift'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Employee Working Shift'

    name = fields.Char(string='Name', required=True)
    shift_mode = fields.Selection([('employee', 'By Employee'), ('department', 'By Department'),
                                   ('company', 'By Company')], default='company', string='Mode',
                                  required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee')
    department_id = fields.Many2one('hr.department', string='Department')
    company_id = fields.Many2one('res.company', string='Company')
    active = fields.Boolean(string='Active', default=True)
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    shift_type_id = fields.Many2one('resource.calendar', string='Shift Type',
                                    required=True)
    description = fields.Text(string='Description')
    state = fields.Selection([('draft', 'Draft'), ('submit', 'Submitted'),
                              ('approve', 'Approved'), ('cancel', 'Cancelled'), ('reject', 'Rejected')],
                             default='draft', string='State')

    def action_submit(self):
        self.check_deplicate_rule()
        self.state = 'submit'

    def action_approve(self):
        self.check_deplicate_rule()
        self.state = 'approve'

    def action_cancel(self):
        self.state = 'cancel'

    def action_reject(self):
        self.state = 'reject'

    @api.constrains('active', 'start_date', 'end_date')
    def check_deplicate_rule(self):
        for record in self:
            existing_shift = self.env['hr.employee.shift'].search(
                [('id', '!=', record.id), ('state', '=', 'approve'),
                 ('start_date', '>=', record.start_date),
                 ('end_date', '<=', record.end_date)])
            if record.shift_mode == 'company':
                existing_company_shift = existing_shift.filtered(lambda shift: shift.shift_mode == 'company' and
                                                                                       shift.company_id == record.company_id)
                if existing_company_shift:
                    raise ValidationError(_("1 Other shift for this company at the same time\n"
                                            "please delete or archive it!"))
            elif record.shift_mode == 'department':
                existing_department_shift = existing_shift.filtered(lambda shift: shift.shift_mode == 'department' and
                                                                                       shift.department_id == record.department_id)
                if existing_department_shift:
                    raise ValidationError(_("1 Other shift for this department at the same time\n"
                                            "please delete or archive it!"))
            elif record.shift_mode == 'employee':
                existing_department_shift = existing_shift.filtered(lambda shift: shift.shift_mode == 'employee' and
                                                                                  shift.employee_id == record.employee_id)
                if existing_department_shift:
                    raise ValidationError(_("1 Other shift for this employee at the same time\n"
                                            "please delete or archive it!"))
            else:
                pass

    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise ValidationError(_("You can't delete record not in draft state!"))
            return super(HrEmployeeShift, self).unlink()
