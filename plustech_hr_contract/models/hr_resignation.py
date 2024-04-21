# -*- coding: utf-8 -*-
import datetime
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
date_format = "%Y-%m-%d"
RESIGNATION_TYPE = [('resigned', 'Normal Resignation'),
                    ('fired', 'Fired by the company'),
                    ('Unwillingness', 'UnwillingnessTO Renew Contract')]
SALARY_TYPE = [('monthly', 'Monthly'), ('other', 'Other')]


class HrResignation(models.Model):
    _name = 'hr.resignation'
    _description = 'Resignation'

    name = fields.Char()


class HrEmployeeResignation(models.Model):
    _name = 'hr.employee.resignation'
    _inherit = 'mail.thread'
    _rec_name = 'employee_id'
    _description = 'Employee Resignation'

    name = fields.Char(string='Request Reference', required=True, copy=False, readonly=True, index=True,
                       default=lambda self: _('New'))
    employee_id = fields.Many2one('hr.employee', string="Employee", default=lambda self: self.env.user.employee_id.id,
                                  help='Name of the employee for whom the request is creating')
    department_id = fields.Many2one('hr.department', string="Department", related='employee_id.department_id',
                                    help='Department of the employee')

    approved_date = fields.Date(string="Approved Date",
                                help='Date on which the request is approved by the manager.',
                                tracking=True)

    expected_leaving_date = fields.Date(string="Last Day of Employee", required=True,
                                        help='Employee requested date on which he is leaving  the company.')
    reason = fields.Text(string="Reason", required=True,
                         help='Specify reason for leaving the company')
    notice_period = fields.Integer(string="Notice Period")
    state = fields.Selection(
        [('draft', 'Draft'), ('inform', 'Informed'),
         ('approved', 'Approved'), ('cancel', 'Rejected')],
        string='Status', default='draft', tracking=True)
    resignation_type = fields.Selection(selection=RESIGNATION_TYPE, help="Select the type of resignation: normal "
                                                                         "resignation or fired by the company")
    salary_type = fields.Selection(selection=SALARY_TYPE, default="monthly",
                                   help="Select the type of salary: monthly salary or others(yearly ,weekly ,..ext)")
    company_id = fields.Many2one(
        'res.company', string="Company", default=lambda self: self.env.company)

    @api.model
    def create(self, vals):
        # assigning the sequence for the record
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'hr.resignation') or _('New')
        res = super(HrEmployeeResignation, self).create(vals)
        return res

    @api.onchange('salary_type')
    def _onchange_salary_type(self):
        get_param = self.env['ir.config_parameter'].sudo().get_param
        for rec in self:
            if rec.salary_type == 'monthly':
                rec.notice_period = get_param(
                    'saudi_hr_contract.no_of_days_monthly')
            elif rec.salary_type == 'other':
                rec.notice_period = get_param(
                    'saudi_hr_contract.no_of_days_other')

    def cancel_resignation(self):
        for rec in self:
            rec.state = 'cancel'

    def reject_resignation(self):
        for rec in self:
            rec.state = 'cancel'

    def reset_to_draft(self):
        for rec in self:
            rec.state = 'draft'
            rec.employee_id.active = True

    def resignation_inform(self):
        for rec in self:
            days = (rec.expected_leaving_date - datetime.now().date()).days
            if days < int(rec.notice_period):
                raise ValidationError(
                    _("You must submit your resignation before %s days") % (rec.notice_period))
            rec.state = 'inform'

    def approve_resignation(self):
        for rec in self:
            if rec.expected_leaving_date:
                no_of_contract = self.env['hr.contract'].search(
                    [('employee_id', '=', self.employee_id.id)])
                for contracts in no_of_contract:
                    if contracts.state == 'open':
                        rec.state = 'approved'
                        no_of_contract.state = 'close'
                        rec.approved_date = datetime.now().date()
                if rec.expected_leaving_date <= fields.Date.today() and rec.employee_id.active:
                    rec.employee_id.active = False
                    # Removing and deactivating user
                    if rec.employee_id.user_id:
                        rec.employee_id.user_id.active = False
                        rec.employee_id.user_id = None
