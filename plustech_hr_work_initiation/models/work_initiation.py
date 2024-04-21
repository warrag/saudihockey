from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta


class EmployeeJoiningApproval(models.Model):
    _name = 'hr.work.initiation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Employee Work Initiation'

    name = fields.Char()
    employee_id = fields.Many2one('hr.employee', string='Employee', default=lambda self: self.env.user.employee_id,
                                  required=True)
    employee_no = fields.Char('Employee No', related='employee_id.employee_id')
    department_id = fields.Many2one('hr.department', string='Department Name', related='employee_id.department_id')
    job_id = fields.Many2one('hr.job', string='Job Title', related='employee_id.job_id')
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.user.company_id.id)
    request_date = fields.Date(string='Request Date', default=fields.Date.today())
    attachment_number = fields.Integer('Number of Attachments', compute='get_attachment_ids')
    description = fields.Text(string='Description')
    joining_date = fields.Date(string='Joining Date', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('direct_manager', 'Waiting for Direct Manager Approval'),
        ('hr', 'Waiting for HR Report'),
        ('admin', 'Waiting for  Director of Financial and Administrative Affairs Approval'),
        ('validate', 'Approved'),
        ('cancel', 'Cancelled'),
        ('refuse', 'Refused'),
    ], string='Status', readonly=True, tracking=True, copy=False, default='draft',
    )
    duty_commencement_type_id = fields.Many2one('duty.commencement.type', string='Duty Commencement Type')
    commencement_status = fields.Selection([('on-time', 'On Time'), ('late', 'Late')],
                                           string='Commencement Status', default="on-time")
    late_days = fields.Integer(string='Late Days')
    approval_ids = fields.One2many('hr.work.initiation.approvals', 'request_id', string="Approver's")
    manager_id = fields.Many2one('res.users', string='Manager',
                                 related='employee_id.parent_id.user_id')
    is_manager = fields.Boolean(compute='get_current_uid')

    @api.depends('manager_id', 'employee_id')
    def get_current_uid(self):
        """

        :param self:
        :return:
        """
        if self.manager_id.id == self.env.user.id:
            self.is_manager = True
        else:
            self.is_manager = False

    def action_submit(self):
        self._create_activity(self.employee_id.parent_id.user_id)
        self.write({'state': 'direct_manager'})

    def action_manager_approve(self):
        group_id = self.env.ref('hr.group_hr_user').id
        users = self.env['res.users'].search(
            [('groups_id', '=', group_id), ('login', 'not in', ['admin', str(self.env.user.company_id.email)])])
        users = users.filtered(
            lambda user: not user.has_group('hr.group_hr_manager'))
        self._create_activity(users)
        self.sudo().get_user_approval_activities(user=self.env.user).action_feedback()
        self.write({'state': 'hr',
                    'approval_ids': [(0, 0, {'user_id': self.env.user.id, 'name': 'direct_manager_approval',
                                              'state': 'approved', 'date': fields.Date().today()})],
                    })

    def action_hr_approve(self):
        self.sudo().get_user_approval_activities(user=self.env.user).action_feedback()
        self.employee_id.last_annual_leave_status = 'return'
        self.employee_id.last_annual_return_date = self.joining_date
        allocations = self.env['hr.leave.allocation'].sudo().search([
            ('employee_id', 'in', self.ids),
            ('holiday_status_id.is_annual_leave', '=', True),
            ('state', 'not in', ['cancel', 'refuse', 'draft']),
             '|', ('date_to', '=', False), ('date_to', '>', fields.Date.today())
        ])
        for allocation in allocations:
            allocation.nextcall = fields.Date.today() + timedelta(days=1)
        self.write({'state': 'admin',
                    'approval_ids': [(0, 0, {'user_id': self.env.user.id, 'name': 'human_resources_report',
                                             'state': 'approved', 'date': fields.Date().today()})],
                    })

    def action_admin_approve(self):
        self.write({'state': 'validate',
                    'approval_ids': [(0, 0, {'user_id': self.env.user.id,
                                             'name': 'director_of_financial_and_administrative_affairs_approval',
                                             'state': 'approved', 'date': fields.Date().today()})],
                    })

    def _create_activity(self, users):
        for user in users:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                date_deadline=0,
                summary="Work Initiation",
                note="New work initiation need your approval",
                user_id=user.id)

    def get_user_approval_activities(self, user):
        domain = [
            ('res_model', '=', 'hr.work.initiation'),
            ('res_id', 'in', self.ids),
            ('activity_type_id', '=', self.env.ref('mail.mail_activity_data_todo').id),
            ('user_id', '=', user.id)
        ]
        activities = self.env['mail.activity'].search(domain)
        return activities

    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        res['domain'] = [('res_model', '=', 'employee.work.initiation'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'employee.work.initiation', 'default_res_id': self.id}
        return res

    def get_attachment_ids(self):
        for rec in self:
            rec.attachment_number = self.env['ir.attachment'].search_count(
                [('res_model', '=', 'employee.work.initiation'),
                 ('res_id', '=', rec.id)])

    def attach_document(self, **kwargs):
        pass

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            seq_date = None
            if 'request_date' in vals:
                seq_date = fields.Datetime.context_timestamp(
                    self, fields.Datetime.to_datetime(vals['request_date']))
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'employee.work.initiation', sequence_date=seq_date) or _('New')
        result = super(EmployeeJoiningApproval, self).create(vals)
        return result

    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise ValidationError(_("You can't delete record not in draft stage"))
        res = super(EmployeeJoiningApproval, self).unlink()
        return res
