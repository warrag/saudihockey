# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import date
from odoo.addons.plustech_hr_employee.models.tools import convert_gregorian_to_hijri


class PreviousCourses(models.Model):
    _name = 'previous.courses'
    _description = 'Previous Courses'
    course = fields.Char(string='Course Name')
    enrolled_date = fields.Date(string='Enrolled Date')


class TrainingTraining(models.Model):
    _name = 'training.training'
    _description = 'Training'
    _order = 'name desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    def _default_employee(self):
        return self.env.context.get('default_employee_id') or self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)], limit=1)

    name = fields.Char(string='Number#', default='New')
    training_type = fields.Selection(selection=[('internal', 'Internal'), ('external', 'External')],
                                     default='internal', string='Training Type', tracking=True,
                                     required=True)
    country_id = fields.Many2one('res.country', string='Destination Country')
    city_id = fields.Many2one('res.city', string='Destination City',
                              domain="[('country_id', '=', country_id)]")
    course_id = fields.Many2one('course.schedule', string='Course',
                                domain=[('state', '=', 'active')])
    course_name = fields.Char(string='Course Name', related='course_id.text', store="True", readonly=False)
    price = fields.Float(string='Price', related='course_id.price',
                         store="True", readonly=False)
    amount_currency = fields.Monetary(default=0.0, currency_field='company_currency_id')
    bio_content = fields.Html(string='Contents', related='course_id.bio_cont',
                              store="True", readonly=False)
    requirements = fields.Html(string='Agreements', related='course_id.requirements', readonly='True')
    goals = fields.Html(string='Agreements', related='course_id.goals',
                        store="True", readonly=False)
    employee_id = fields.Many2one('hr.employee', string='Employee', index=True, readonly=True,
                                  states={'new': [('readonly', False)], 'direct_manager': [('readonly', False)]},
                                  default=_default_employee)
    employee_no = fields.Char(related='employee_id.employee_number', string='Employee Number')
    job_title = fields.Char(related='employee_id.job_title', string='Job Title')
    department_id = fields.Many2one(related='employee_id.department_id', string='Department', store=True)
    joining_date = fields.Date(related='employee_id.join_date', string='Joining Date')
    phone = fields.Char(related='employee_id.work_phone', string='Phone')
    email = fields.Char(related='employee_id.work_email', string='Email')
    request_date = fields.Date(default=fields.Date.today(), string='Request Date')
    bio_agreement = fields.Html(string='Agreements', related='course_id.bio', readonly='True')
    state = fields.Selection(selection=[('new', 'New'),  ('direct_manager', 'Waiting Manager Approval'),
                                        ('officer', 'Waiting Human Resource Officer Approval'),
                                        ('hr', 'Waiting Human Resource Report'),
                                        ('admin', 'Financial and Administrative Affairs Approval'),
                                        ('ceo', 'Waiting CEO Approval'), ('approve', 'Approved'),
                                        ('close', 'Closed'), ('cancel', 'Canceled')], default='new')
    user_id = fields.Many2one('res.users', string='User', related='employee_id.user_id',
                              related_sudo=True, readonly=True)
    training_place = fields.Char(related='course_id.training_place', string='Training Place',
                                 store="True", readonly=False)
    executing_agency_id = fields.Many2one(related='course_id.trainer_id', string='Executing Agency',
                                          store="True", readonly=False)
    start_date = fields.Date(related="course_id.f_date", string='Start Date',
                             store="True", readonly=False)
    end_date = fields.Date(related="course_id.to_date", string='End Date',
                           store="True", readonly=False)
    duration = fields.Integer('Duration', compute='_calc_days', readonly=True)
    course_ids = fields.Many2many('enrolled.student', string='previous Courses',
                                  compute='_get_cat')
    manager_id = fields.Many2one('res.users', string='Manager',
                                      related='employee_id.parent_id.user_id')
    manager_approval_date = fields.Date(string="Approval Date", copy=False)
    hr_officer_user_id = fields.Many2one('res.users', string='Officer', readonly=True)
    hr_officer_confirm_date = fields.Date(string='Approval Date', readonly=True, copy=False)
    hr_manager_user_id = fields.Many2one('res.users', string='Manager', readonly=True)
    hr_confirm_date = fields.Date(string='Approval Date', readonly=True, copy=False)
    general_manager_user_id = fields.Many2one('res.users', string='Manager', readonly=True)
    general_manager_confirm_date = fields.Date(string='Approval Date', readonly=True, copy=False)
    admin_user_id = fields.Many2one('res.users', string='Manager', readonly=True)
    admin_confirm_date = fields.Date(string='Approval Date', readonly=True, copy=False)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency',readonly=False,default=lambda self: self.env.company.currency_id, string='Currency')
    company_currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id,
                                          string='Company Currency')
    attachment_number = fields.Integer('Number of Attachments', compute='get_attachment_ids')
    is_manager = fields.Boolean(compute='get_current_uid')

    @api.depends('start_date', 'end_date')
    def _calc_days(self):
        days = 0
        if self.start_date and self.end_date and self.start_date <= self.end_date:
            delta = self.end_date - self.start_date
            days = delta.days+1
        self.duration = days

    @api.onchange('price','currency_id')
    def _onchange_price(self):
        self.amount_currency = self.currency_id._convert(self.price, self.company_currency_id, self.company_id,
                          self.request_date or fields.Date.context_today(self))

    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        res['domain'] = [('res_model', '=', 'training.training'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'training.training', 'default_res_id': self.id}
        return res

    def get_attachment_ids(self):
        for rec in self:
            rec.attachment_number = self.env['ir.attachment'].search_count([('res_model', '=', 'training.training'),
                                                                            ('res_id', '=', rec.id)])

    def attach_document(self, **kwargs):
        pass

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

    @api.depends("employee_id")
    def _get_cat(self):
        emp_course = self.env['enrolled.student'].search(
            [('employee_id', '=', self.employee_id.id)])
        self.course_ids = emp_course

    def action_submit(self):
        training_activity = self.env['training.training.activity'].sudo().search([('training_state', '=', 'direct_manager')])
        for activity in training_activity:
            self.create_activity(activity, user=self.employee_id.parent_id.user_id)
        self.write({'state': 'direct_manager'})

    def action_manager_approve(self):
        self._action_feedback_activity(self.state)
        self.write({'state': 'officer',
                    'manager_approval_date': date.today(),
                    'manager_id': self.env.user.id
                    })
        ticket_activity = self.env['training.training.activity'].sudo().search([('training_state', '=', 'officer')])
        for activity in ticket_activity:
            self.create_activity(activity)

    def action_hr_officer_approve(self):
        self._action_feedback_activity(self.state)
        self.write({'state': 'hr',
                    'hr_officer_confirm_date': date.today(),
                    'hr_officer_user_id': self.env.user.id
                    })
        ticket_activity = self.env['training.training.activity'].sudo().search([('training_state', '=', 'hr')])
        for activity in ticket_activity:
            self.create_activity(activity)

    def action_hr_approve(self):
        self._action_feedback_activity(self.state)
        self.write({'state': 'admin',
                    'hr_confirm_date': date.today(),
                    'hr_manager_user_id': self.env.user.id
                    })
        ticket_activity = self.env['training.training.activity'].sudo().search([('training_state', '=', 'admin')])
        for activity in ticket_activity:
            self.create_activity(activity)

    def action_admin_approve(self):
        self._action_feedback_activity(self.state)
        self.write({'state': 'ceo',
                    'admin_confirm_date': date.today(),
                    'admin_user_id': self.env.user.id
                    })
        ticket_activity = self.env['training.training.activity'].sudo().search([('training_state', '=', 'ceo')])
        for activity in ticket_activity:
            self.create_activity(activity)

    def action_ceo_approve(self):
        self._action_feedback_activity(self.state)
        values = {'enrolled_date': fields.Date.today(), 'employee_id': self.employee_id.id}
        new_record = [(0, 0, values)]
        for rec in self:
            rec.course_id.registered_employees = new_record
        self.write({'state': 'approve',
                    'general_manager_confirm_date': date.today(),
                    'general_manager_user_id': self.env.user.id
                    })

    def action_close(self):
        self.state = 'close'

    def action_cancel(self):
        self.state = 'cancel'

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            seq_date = None
            if 'request_date' in vals:
                seq_date = fields.Datetime.context_timestamp(
                    self, fields.Datetime.to_datetime(vals['request_date']))
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'training.request', sequence_date=seq_date) or _('New')
        result = super(TrainingTraining, self).create(vals)

        return result

    def convert_gregorian_to_hijri(self, date):
        return convert_gregorian_to_hijri(date)

    def create_activity(self, activity, user=False, ):
        if activity:
            for obj in activity:
                users_id = obj.users_id or user
                self.env['mail.activity'].sudo().create({
                    'activity_type_id': obj.activity_type_id.id,
                    'res_id': self.id,
                    'res_model_id': self.env['ir.model'].sudo().search([('model', '=', 'training.training')],
                                                                       limit=1).id,
                    'icon': 'fa-pencil-square-o',
                    'date_deadline': fields.Date.today(),
                    'user_id': users_id.id,
                    'summary': obj.subject if obj.subject else False,
                    'note': obj.note,
                })

    def _action_feedback_activity(self, state):
        for record in self:
            previous_training_activity = self.env['training.training.activity'].sudo().search(
                [('training_state', '=', state)])
            for activity in previous_training_activity:
                self.sudo()._get_user_approval_activities(user=self.env.user,
                                                          activity_type=activity.activity_type_id,
                                                          record=record).action_feedback()

    def _get_user_approval_activities(self, user=False, activity_type=False, record=False):
        domain = [
            ('res_model', '=', 'training.training'),
            ('res_id', 'in', record.ids),
            ('activity_type_id', '=', activity_type.id)]
        activities = self.env['mail.activity'].search(domain)
        return activities
