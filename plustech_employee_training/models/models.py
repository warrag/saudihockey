# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import timedelta
from odoo.exceptions import ValidationError



class EnrolledStudent(models.Model):
    _name = 'enrolled.student'
    _description = 'Enrolled Student'

    employee_id = fields.Many2one('hr.employee', string='Employee')
    enrolled_date = fields.Date(default=fields.Date.today(), string='Enrolled Date')
    student_name = fields.Many2one('course.schedule')
    hours = fields.Float(string='Attending Hours')


class CourseSchedule(models.Model):
    _name = 'course.schedule'
    _description = 'Course Schedule'
    _inherit = ['mail.thread']
    _rec_name = 'text'

    def calc_remain(self):
        if self.capacity or self.reserve:
            if self.capacity >= self.reserve:
                self.remain = self.capacity - self.reserve
            else:
                self.remain = 0

    def compute_reserve(self):
        calc_reserve = self.env['training.training']
        for sch in self:
            sch.reserve = calc_reserve.search_count(
                [('course_id.id', '=', sch.id), ('state', '!=', 'cancel'), ('state', '!=', 'new')])
            if sch.reserve == sch.capacity:
                sch.write({'state': 'close'})
            elif sch.reserve < sch.capacity:
                sch.write({'state': 'active'})
            return

    @api.onchange('f_date', 'to_date')
    def _calc_days(self):
        if self.f_date and self.to_date and self.f_date <= self.to_date:
            res = self.to_date - self.f_date
            self.duration = int(res.days)+1

    course_id = fields.Many2one('course.training', string='Course', required='1')
    currency_id = fields.Many2one('res.currency', related="course_id.currency_id",
                                  readonly=False, string='Currency')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    company_currency_id = fields.Many2one('res.currency', related="company_id.currency_id", string='Company Currency')
    duration = fields.Integer('Duration')
    f_date = fields.Date(string='From')
    to_date = fields.Date(string='To')
    capacity = fields.Integer(string='Capacity', default=1, required=1)
    tags = fields.Many2many('hr.employee.category', 'sch_category_rel', 'sch_id', 'category_id', string='Tags')
    price = fields.Float(string='Price', related='course_id.price_ids', readonly=True)
    trainer_id = fields.Many2one('res.partner', domain=[('is_trainer', '=', True)], string='Executing Agency')
    reserve = fields.Integer(string='Reservation', compute='compute_reserve')
    remain = fields.Integer(string='Remaining', compute='calc_remain')
    bio = fields.Html(string='Bio', related='agreement_template_id.agreement_content')
    state = fields.Selection(selection=[('new', 'New'), ('active', 'Active'), ('close', 'Closed')
                                        ], default='new', tracking=True)
    text = fields.Char(string='Cou', related='course_id.course')
    requirements = fields.Html('Bio', related='course_id.requirements')
    goals = fields.Html('Bio', related='course_id.goals')
    bio_cont = fields.Html('Bio', related='course_id.bio_course')
    training = fields.One2many('training.training', 'course_id', string='Train')
    registered_employees = fields.One2many('enrolled.student', 'student_name', string='Employees')
    training_place = fields.Char(string='Training Place')
    paid_by = fields.Selection([('company', 'Company'), ('employee', 'Employee')], string="Paying By", default="company")
    invoice_count = fields.Integer(string='Invoice Count', compute='_get_invoiced')
    payslip_paid = fields.Boolean(default=False)
    agreement_template_id = fields.Many2one('course.agreement.template', string='Agreement template')
    hours_per_day = fields.Float(string='Hours Per Days')
    schedule_ids = fields.One2many('training.time.table', 'course_id')

    def generate_schedule(self):
        self.schedule_ids = None
        schedule_obj = self.env['training.time.table']
        delta = self.to_date - self.f_date
        days = self.get_period_days(self.f_date, delta)
        lines = []
        hours = self.hours_per_day
        for day in days:
            vals = {
                'date': day,
                'course_id': self.id,
                'week_day': f'{day.weekday()}',
                'hours': hours
            }
            lines.append(vals)
        schedule_obj.create(lines)

    def get_period_days(self, date_from, delta):
        all_period_date = []
        for i in range(delta.days + 1):
            day = date_from + timedelta(days=i)
            all_period_date.append(day)
        return all_period_date

    def _get_invoiced(self):
        for rec in self:
            invoices = invoices = self.env['account.move'].search([('course_id', '=', rec.id)])
            rec.invoice_count = len(invoices)

    def action_new(self):
        self.state = 'new'

    def action_active(self):
        self.state = 'active'

    def action_close(self):
        self.state = 'close'
        training_requests = self.env['training.training'].search([('course_id', '=', self.id),
                                                                  ('state', '=', 'approve')])
        for rec in training_requests:
            rec.action_close()

    def action_create_bill(self):
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        form_view = [(self.env.ref('account.view_move_form').id, 'form')]
        if 'views' in action:
            action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
        else:
            action['views'] = form_view
        invoice_vals_list = {
            'user_id': self.env.user.id,
            'course_id': self.id,
            'move_type': 'in_invoice',
            'partner_id': self.trainer_id.id,
            'invoice_line_ids': self._prepare_invoice_lines()
        }
        invoices = self.env['account.move'].sudo().create(
            invoice_vals_list)
        action['res_id'] = invoices.id
        return action

    def _default_product_id(self):
        return self.env.user.company_id.training_product_id

    def _default_analytic_account_id(self):
        analytic_account_id = self.env.user.company_id.training_analytic_account_id
        return analytic_account_id

    def _prepare_invoice_lines(self):
        amount = self.price * len(self.registered_employees)
        product_id = self._default_product_id()
        if not product_id:
            raise ValidationError(_('Please set the product up for creating the bill'))
        analytic_account_id = self._default_analytic_account_id()
        invoice_lines = [(0, 0, {
            'name': 'Course: %s From %s To %s' % (self.course_id.course, self.f_date, self.to_date),
            'price_unit': amount,
            'quantity': 1.0,
            'product_id': product_id.id,
            'analytic_account_id': analytic_account_id.id,

        })]
        return invoice_lines

    def action_view_invoice(self):
        invoices = self.env['account.move'].search([('course_id', '=', self.id)])
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        context = {
            'default_move_type': 'in_invoice',
        }
        if len(self) == 1:
            context.update({
                'default_partner_id': self.trainer_id.id,
                'user_id': self.env.user.id,
            })
        action['context'] = context
        return action


class CourseTraining(models.Model):
    _name = 'course.training'
    _description = 'Course Training'
    _inherit = ['mail.thread']
    _rec_name = 'course'

    course = fields.Char(string='Course Name', required='1', translate=True)
    code = fields.Char(string='Code',size=5)
    bio_course = fields.Html('Bio')
    goals = fields.Html('Goals')
    requirements = fields.Html('Goals')
    price_ids = fields.Float(string='Price', required='1')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id, string='Currency')
    _sql_constraints = [
        ('course_code_unique',
         'UNIQUE(code)',
         _('Code Must be Unique')),
    ]


class AccountMove(models.Model):
    _inherit = 'account.move'

    course_id = fields.Many2one(
        string='Course',
        comodel_name='course.schedule',
        ondelete='restrict',
    )
