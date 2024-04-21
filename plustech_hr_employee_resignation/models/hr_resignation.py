# -*- coding: utf-8 -*-
import datetime
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

date_format = "%Y-%m-%d"
RESIGNATION_TYPE = [('resigned', 'Normal Resignation'),
                    ('fired', 'Fired by the company'),
                    ('unwillingness', 'Unwillingness TO Renew Contract'),
                    ('termination', 'Contract Termination'),
                    ]


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
    employee_no = fields.Char(related='employee_id.employee_number')
    department_id = fields.Many2one('hr.department', string="Department", related='employee_id.department_id',
                                    help='Department of the employee')

    approved_date = fields.Date(string="Approved Date",
                                help='Date on which the request is approved by the manager.',
                                tracking=True)
    request_date = fields.Date(string="Request Date", required=True, default=fields.Date.today())
    expected_leaving_date = fields.Date(string="Last Day of Employee", required=True,
                                        help='Employee requested date on which he is leaving  the company.')
    reason = fields.Text(string="Reason", required=True,
                         help='Specify reason for leaving the company')
    state = fields.Selection(
        [('draft', 'Draft'), ('dm_approval', 'Direct Manager Approval'),
         ('hr_approval', 'HR Approval'), ('approved', 'Approved'), ('cancel', 'Rejected')],
        string='Status', default='draft', tracking=True)
    resignation_type = fields.Selection(selection=RESIGNATION_TYPE, help="Select the type of resignation: normal "
                                                                         "resignation or fired by the company",
                                        default='fired')
    company_id = fields.Many2one(
        'res.company', string="Company", default=lambda self: self.env.company)
    notice_start = fields.Date(string='Start Date')
    notice_end = fields.Date(string='End Date')
    manager_id = fields.Many2one('res.users', related='employee_id.parent_id.user_id')
    is_manager = fields.Boolean(string='Is Manager', compute='compute_is_manager')
    count_eos = fields.Integer(string='End Of Service Count', compute='count_end_of_service')
    contract_id = fields.Many2one('hr.contract', related='employee_id.contract_id', string='Current Contract')
    contract_end_date = fields.Date(related='contract_id.date_end')

    def count_end_of_service(self):
        for record in self:
            eos_ids = self.env['end.of.service.reward'].search([('resignation_id', '=', record.id)])
            record.count_eos = len(eos_ids)

    @api.depends('manager_id')
    def compute_is_manager(self):
        for record in self:
            if record.manager_id == self.env.user:
                record.is_manager = True
            else:
                record.is_manager = False

    @api.model
    def create(self, vals):
        # assigning the sequence for the record
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'hr.resignation') or _('New')
        res = super(HrEmployeeResignation, self).create(vals)
        return res

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

    def resignation_submit(self):
        for rec in self:
            rec.state = 'dm_approval'

    def action_manager_approval(self):
        self.state = 'hr_approval'

    def action_hr_approval(self):
        self.state = 'approved'

    def action_generate_eos(self):
        result = self.env.ref('plustech_hr_end_of_service.end_of_service_award_action').read()[0]
        view_id = self.env.ref('plustech_hr_end_of_service.view_end_of_service_award_form').id
        result.update({'views': [(view_id, 'form')], })
        result['context'] = {
            'default_employee_id': self.employee_id.id,
            'default_resignation_id': self.id,
            'default_last_work_date': self.notice_end
        }
        return result

    def action_open_eos(self):
        self.ensure_one()
        action, = self.env.ref('plustech_hr_end_of_service.end_of_service_award_action').read()
        action['domain'] = [('resignation_id', '=', self.id)]
        return action

    def action_open_contract(self):
        self.ensure_one()
        action, = self.env.ref('hr_contract.action_hr_contract').read()
        action['domain'] = [('id', '=', self.contract_id.id)]
        return action

