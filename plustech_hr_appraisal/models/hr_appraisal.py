# -*- coding: utf-8 -*-

import datetime
import logging

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.misc import format_date
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class HrAppraisal(models.Model):
    _name = "hr.appraisal.appraisal"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Employee Appraisal"
    _order = 'state desc, id desc'
    _rec_name = 'employee_id'
    _mail_post_access = 'read'

    @api.model
    def create(self, vals):
        res = super(HrAppraisal, self).create(vals)
        for rec in res:
            for emp in rec.employee_id:
                recipient_partners = []
                if emp.user_id and emp.user_id.partner_id:
                    recipient_partners.append(emp.user_id.partner_id.id)
                group_id = self.env.ref('hr.group_hr_user').id
                user_ids = self.env['res.users'].search([('groups_id', '=', group_id)])
                for user in user_ids:
                    if user.partner_id:
                        if user.partner_id:
                            recipient_partners.append(user.partner_id.id)
                for partner in recipient_partners:
                    vals = {
                        'subject': "Created Appraisal Notification",
                        'body': "New Appraisal Created...",
                        'res_id': rec.id,
                        'model': 'hr.appraisal.appraisal',
                        'message_type': 'notification',
                        'partner_ids': [(4, partner)]
                    }
                    message_ids = self.env['mail.message'].create(vals)
                    message = self.env['mail.notification'].create({'mail_message_id': message_ids.id, 'res_partner_id': partner})
        return res
    
    
    def cron_create_appraisal(self):
        create_appraisal = self.env['ir.config_parameter'].sudo().get_param('plustech_hr_appraisal.create_appraisal')
        appraisal_type = self.env['ir.config_parameter'].sudo().get_param('plustech_hr_appraisal.appraisal_type')
        today = datetime.now().date()
        # if today.day == 1 and today.month == 1:
        print(appraisal_type)
        print(create_appraisal)
        if appraisal_type != "False":
            if create_appraisal == 'automatically':
                month = 0
                if appraisal_type == '1':
                    month = 1
                if appraisal_type == '4':
                    month = 3
                if appraisal_type == '6':
                    month = 6
                if appraisal_type == '12':
                    month = 1
                for emp in self.env['hr.employee'].search([]):
                    new_appraisal = self.env['hr.appraisal.appraisal'].create({
                        'type': appraisal_type,
                        'parent_id': False,
                        'last_one': False,
                        'employee_id': emp.id,
                        'start_date': today,
                        'end_date': today + relativedelta(months=+month),
                        'appraisal_tmp_id': emp.job_id.appraisal_tmp_id.id,
                    })
                    new_appraisal.change_employee_get_assignment_date()
                    new_appraisal.change_type()
                    # if emp.user_id.partner_id:
                    #     vals = {
                    #         'subject': "Created Appraisal Notification",
                    #         'body': "New Appraisal Created...",
                    #         'res_id': new_appraisal.id,
                    #         'model': 'hr.appraisal.appraisal',
                    #         'message_type': 'notification',
                    #         'partner_ids': [(4, emp.user_id.partner_id.id)]
                    #     }
                    #     message_ids = self.env['mail.message'].create(vals)
                    #     self.env['mail.notification'].create({'mail_message_id': message_ids.id, 'res_partner_id': emp.user_id.partner_id.id})

    def _get_default_employee(self):
        if self.env.context.get('active_model') in (
                'hr.employee', 'hr.employee.public') and 'active_id' in self.env.context:
            return self.env.context.get('active_id')
        elif self.env.context.get('active_model') == 'res.users' and 'active_id' in self.env.context:
            return self.env['res.users'].browse(self.env.context['active_id']).employee_id
        if not self.env.user.has_group('hr.group_hr_user'):
            return self.env.user.employee_id

    annual_ids = fields.One2many(comodel_name='hr.appraisal.line', inverse_name='annual_appraisal_id')
    competencies_ids = fields.One2many(comodel_name='hr.appraisal.line', inverse_name='competencies_appraisal_id')
    active = fields.Boolean(default=True)
    appraisal_tmp_id = fields.Many2one('hr.appraisal.template', required=True, string='Appraisal Template')
    employee_id = fields.Many2one('hr.employee', required=True, string='Employee', index=True,
                                  default=_get_default_employee)
    employee_user_id = fields.Many2one('res.users', string="Employee User", related='employee_id.user_id')
    batch_id = fields.Many2one('hr.appraisal.batch', string="Appraisal Batch")
    employee_number = fields.Char(string='Employee No#', related='employee_id.employee_number')
    join_date = fields.Date(string='Employment Date', related='employee_id.join_date')
    company_id = fields.Many2one('res.company', related='employee_id.company_id', store=True)
    department_id = fields.Many2one(
        'hr.department', related='employee_id.department_id', string='Department', store=True)
    job_id = fields.Many2one('hr.job', related='employee_id.job_id', string='Job Position')
    join_date = fields.Date(related='employee_id.join_date', string='Joining Date')
    pin = fields.Char(related='employee_id.employee_number', string='Number')
    assignment_date = fields.Date(string='Assignment Date')
    image_128 = fields.Image(related='employee_id.image_128')
    image_1920 = fields.Image(related='employee_id.image_1920')
    avatar_128 = fields.Image(related='employee_id.avatar_128')
    avatar_1920 = fields.Image(related='employee_id.avatar_1920')
    # last_appraisal_id = fields.Many2one('hr.appraisal', related='employee_id.last_appraisal_id')
    # last_appraisal_date = fields.Date(related='employee_id.last_appraisal_date')
    previous_appraisal_id = fields.Many2one('hr.appraisal.appraisal')
    # uncomplete_goals_count = fields.Integer(related='employee_id.uncomplete_goals_count')
    objectives_percentage = fields.Float(string='Objectives Percentage',
                                         related="appraisal_tmp_id.objectives_percentage")
    competencies_percentage = fields.Float(string='Competencies Percentage',
                                           related='appraisal_tmp_id.competencies_percentage')
    min_objectives = fields.Integer(string='Min Objectives', help="Minimum number of annual objectives",
                                    related="appraisal_tmp_id.min_objectives")
    min_competencies = fields.Integer(string='Min Competencies', help="Minimum number of competencies",
                                      related="appraisal_tmp_id.min_competencies")
    max_objectives = fields.Integer(string='Max Objectives', help="Maximum number of annual objectives",
                                    related="appraisal_tmp_id.max_objectives")
    max_competencies = fields.Integer(string='Max Competencies', help="Maximum number of competencies",
                                      related="appraisal_tmp_id.max_competencies")
    objective_total = fields.Float(string="Objectives %", compute="get_objective_total")
    competencies_total = fields.Float(string="Competencies %", compute="get_competencies_total")
    total = fields.Float(string="Total %", compute="get_total")
    total_percentage = fields.Float(string="Total %", compute="get_total")
    final_classification_id = fields.Many2one('hr.appraisal.evaluation.scale', compute="get_classification")
    parent_id = fields.Many2one('hr.appraisal.appraisal', string='Parent')
    child_ids = fields.One2many('hr.appraisal.appraisal', 'parent_id', 'Children')
    last_one = fields.Boolean()
    def get_appraisal_type(self):
        return self.env['ir.config_parameter'].sudo().get_param('plustech_hr_appraisal.appraisal_type')

    type = fields.Selection(string='Type', selection=[
        ('1', 'Monthly'),
        ('3', 'quarterly'),
        ('6', 'Semi'),
        ('12', 'Annually'),
    ], default=get_appraisal_type, required=True, )
    start_date = fields.Date(string='Start Date', default=datetime.now().date().replace(month=1, day=1))
    end_date = fields.Date(string='End Date', )
    deadline_date = fields.Date(string='Deadline Date', )
    can_confirm = fields.Boolean(compute="compute_can_confirm")
    can_approve_hr1 = fields.Boolean(compute="compute_can_approve_hr")
    can_approve_hr2 = fields.Boolean(compute="compute_can_approve_hr")

    def _compute_access_url(self):
        super(HrAppraisal, self)._compute_access_url()
        for order in self:
            order.access_url = '/my/appraisal/%s' % (order.id)
    def get_portal_url(self):
        if self:
            portal_url = self[0].get_base_url()
        else:
            portal_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        # portal_link = "%s/?db=%s" % (portal_url, self.env.cr.dbname)
        portal_link = "%s/my/appraisal/%s" % (portal_url, self.id)

        print("XXXXXXXXXXXXXXXXXXXXX ", portal_link)
        return portal_link
    @api.depends('appraiser_id')
    def compute_can_approve_hr(self):
        for rec in self:
            rec.can_approve_hr1  = rec.env.user.has_group('hr.group_hr_user')
            rec.can_approve_hr2  = rec.env.user.has_group('hr.group_hr_manager')

    @api.depends('appraiser_id')
    def compute_can_confirm(self):
        for rec in self:
            rec.can_confirm = True if rec.env.user == rec.appraiser_id.user_id else False

    @api.onchange('type', 'appraisal_tmp_id', 'start_date')
    def change_type(self):
        for rec in self:
            if rec.type == '1':
                rec.end_date = (rec.start_date + relativedelta(months=+1, days=-1)) if rec.start_date else False
            if rec.type == '3':
                rec.end_date = (rec.start_date + relativedelta(months=+3, days=-1)) if rec.start_date else False
            if rec.type == '6':
                rec.end_date = (rec.start_date + relativedelta(months=+6, days=-1)) if rec.start_date else False
            if rec.type == '12':
                rec.end_date = (rec.start_date + relativedelta(months=+12, days=-1)) if rec.start_date else False
            if rec.appraisal_tmp_id:
                rec.deadline_date = rec.end_date + timedelta(days=-rec.appraisal_tmp_id.deadline_reminder) \
                    if rec.end_date and rec.appraisal_tmp_id.deadline_reminder else False

    def action_submit(self):
        self.check_constrains()
        self.state = 'submit'

    def action_confirm(self):
        self.check_constrains()
        self.accept_edit()
        self.state = 'pending'

    def action_approve1(self):
        self.state = 'approve1'

    def action_approve2(self):
        self.state = 'approve2'

    def action_done(self):
        self.check_constrains()
        self.accept_edit()
        self.state = 'done'

    def action_close(self):
        # new_appraisal = self.env['hr.appraisal.appraisal'].create({
        #     'type' : self.type,
        #     'parent_id' : self.id,
        #     'last_one' : True,
        #     'employee_id' : self.employee_id.id,
        #     'start_date' : self.end_date + relativedelta(days=+1) ,
        #     'appraisal_tmp_id' : self.appraisal_tmp_id.id,
        # })
        # new_appraisal.change_employee_get_assignment_date()
        # new_appraisal.change_type()
        # for line in self.annual_ids:
        #     self.env['hr.appraisal.line'].create({
        #         'annual_appraisal_id' : new_appraisal.id,
        #         'type' : 'objective',
        #         'evaluation_id' : line.evaluation_id.id,
        #         'weight_id' : line.weight_id.id,
        #     })
        # for cline in self.competencies_ids:
        #     self.env['hr.appraisal.line'].create({
        #         'competencies_appraisal_id' : new_appraisal.id,
        #         'type' : 'competencies',
        #         'evaluation_id' : cline.evaluation_id.id,
        #         'weight_id' : cline.weight_id.id,
        #     })
        # self.last_one = False
        self.state = 'close'

    def accept_edit(self):
        for rec in self:
            for annual in rec.annual_ids:
                if annual.accept != True:
                    annual.accept = True
                    annual.last_history_id = False
            for competencies in rec.competencies_ids:
                competencies.accept = True
                competencies.last_history_id = False

    def action_refuse(self):
        for rec in self:
            for annual in rec.annual_ids:
                if annual.accept != True:
                    annual.evaluation_id = annual.last_history_id.old_evaluation_id
                    annual.weight_id = annual.last_history_id.old_weight_id.id
                    annual.accept = True
                    annual.last_history_id = False
            for competencies in rec.competencies_ids:
                if competencies.accept != True:
                    competencies.evaluation_id = competencies.last_history_id.old_evaluation_id
                    competencies.weight_id = competencies.last_history_id.old_weight_id.id
                    competencies.accept = True
                    competencies.last_history_id = False
            message = _("Refuse Appraisal Edit ")
            recipient_partners = []
            for emp in rec.employee_id:
                if emp.user_id.partner_id:
                    recipient_partners.append(emp.user_id.partner_id.id)
                    vals = {
                        'subject': "Refuse Appraisal Edit Notification",
                        'body': message,
                        'res_id': rec.id,
                        'model': 'hr.appraisal.appraisal',
                        'message_type': 'notification',
                        'partner_ids': [(4, emp.user_id.partner_id.id)]
                    }
                    message_ids = self.env['mail.message'].create(vals)
                    self.env['mail.notification'].create(
                        {'mail_message_id': message_ids.id, 'res_partner_id': emp.user_id.partner_id.id})
        self.state = 'refuse'

    @api.depends('appraisal_tmp_id')
    def get_classification(self):
        for rec in self:
            rec.final_classification_id = False
            if rec.appraisal_tmp_id:
                if rec.appraisal_tmp_id.evaluation_escale_ids.filtered(
                        lambda m: m.rate_to >= rec.total and m.rate_from <= rec.total):
                    rec.final_classification_id = rec.appraisal_tmp_id.evaluation_escale_ids.filtered(
                        lambda m: m.rate_to >= rec.total and m.rate_from <= rec.total)[0].id

    @api.depends('annual_ids')
    def get_objective_total(self):
        for rec in self:
            rec.objective_total = sum(line.final_score for line in rec.annual_ids)

    @api.depends('competencies_ids')
    def get_competencies_total(self):
        for rec in self:
            rec.competencies_total = sum(line.final_score for line in rec.competencies_ids)

    @api.depends('competencies_ids', 'annual_ids', 'objectives_percentage', 'competencies_percentage')
    def get_total(self):
        for rec in self:
            objective_total = sum(line.final_score for line in rec.annual_ids)
            competencies_total = sum(line.final_score for line in rec.competencies_ids)
            rec.total = objective_total + competencies_total
            rec.total_percentage = rec.objectives_percentage + rec.competencies_percentage

    def check_constrains(self):
        for rec in self:
            if rec.appraisal_tmp_id.min_objectives > len(rec.annual_ids.ids):
                raise UserError(
                    _("Annual Objective count must Bigger than Min Objectives %s lines" % rec.appraisal_tmp_id.min_objectives))
            if rec.appraisal_tmp_id.max_objectives < len(rec.annual_ids.ids):
                raise UserError(
                    _("Annual Objective count must Less than Max Objectives	%s lines" % rec.appraisal_tmp_id.max_objectives))
            if rec.appraisal_tmp_id.min_competencies > len(rec.competencies_ids.ids):
                raise UserError(
                    _("Competencies count must Bigger than Min Objectives %s lines" % rec.appraisal_tmp_id.min_competencies))
            if rec.appraisal_tmp_id.max_competencies < len(rec.competencies_ids.ids):
                raise UserError(
                    _("Competencies count must Less than Max Objectives %s lines" % rec.appraisal_tmp_id.max_competencies))
            if rec.appraisal_tmp_id.objectives_percentage != sum(float(x.weight_id.weight) for x in rec.annual_ids):
                raise UserError(_("Total Objectives Must Equal to %s" % rec.appraisal_tmp_id.objectives_percentage))
            if rec.appraisal_tmp_id.competencies_percentage != sum(
                    float(x.weight_id.weight) for x in rec.competencies_ids):
                raise UserError(_("Total Competencies Must Equal to %s" % rec.appraisal_tmp_id.competencies_percentage))
    @api.constrains('annual_ids', 'competencies_ids')
    def constrains_lines(self):
        for rec in self:
            if rec.annual_ids.mapped('last_history_id') or rec.competencies_ids.mapped('last_history_id'):
                self.check_constrains()
            annual_items = rec.annual_ids.mapped('evaluation_id')
            for eval_item in annual_items:
                if len(rec.annual_ids.filtered(lambda m: m.evaluation_id == eval_item)) > 1:
                    raise UserError(_("Evaluation Objectives [ %s ] Already Exists [ %s ] times" % (
                    eval_item.name, len(rec.annual_ids.filtered(lambda m: m.evaluation_id == eval_item)))))

            competencies_items = rec.competencies_ids.mapped('evaluation_id')
            for competencies_item in competencies_items:
                if len(rec.competencies_ids.filtered(lambda m: m.evaluation_id == competencies_item)) > 1:
                    raise UserError(_("Evaluation in Competencies [ %s ] Already Exists [ %s ] times"
                                      % (competencies_item.name, len(rec.competencies_ids.filtered(
                        lambda m: m.evaluation_id == competencies_item)))))

    @api.onchange('job_id')
    def change_job_id(self):
        for rec in self:
            rec.appraisal_tmp_id = rec.job_id.appraisal_tmp_id.id if rec.job_id else False

    @api.onchange('employee_id')
    def change_employee_get_assignment_date(self):
        for rec in self:
            promotion_id = self.env['employee.promotion'].search([('employee_id', '=', self.employee_id.id)], limit=1)
            rec.assignment_date = rec.promotion_id.effective_date if promotion_id else rec.employee_id.join_date
            self.manager_id = self.employee_id.parent_id.id
            self.appraiser_id = self.employee_id.parent_id.id

    date_close = fields.Date(
        string='Appraisal Date',
        help='Date of the appraisal, automatically updated when the appraisal is Done or Cancelled.', required=True,
        index=True,
        default=lambda self: datetime.today() + relativedelta(months=+1))
    state = fields.Selection([
        ('new', 'Draft'),
        ('submit', 'Submit'),
        ('pending', 'Confirmed'),
        ('edit', 'under modification'),
        ('approve1', 'Appraiser approve'),
        ('approve2', 'Hr approve'),
        ('refuse', 'Refuse'),
        ('done', 'Done'),
        ('cancel', "Cancelled"),
        ('close', "Close"),
    ],
        string='Status', tracking=True, required=True, copy=False,
        default='new', index=True, group_expand='_group_expand_states')
    manager_id = fields.Many2one('hr.employee', context={'active_test': False},
                                 domain="[('active', '=', 'True'), '|', ('company_id', '=', False),"
                                        " ('company_id', '=', company_id)]")
    appraiser_id = fields.Many2one('hr.employee', string="Employee Appraiser")
    # job_id = fields.Many2many('hr.job', string="Job Position", related="employee_id.job_id")
    note = fields.Html(string="Private Note", help="The content of this note is not visible by the Employee.")

    def _group_expand_states(self, states, domain, order):
        return [key for key, val in self._fields['state'].selection]

    can_edit = fields.Boolean(compute="compute_user_edit")
    can_see = fields.Boolean(compute="compute_user_see")
    can_emp_edit = fields.Boolean(compute="compute_emp_edit")

    @api.depends('appraiser_id')
    def compute_emp_edit(self):
        for rec in self:
            rec.can_emp_edit = False
            if self.env.user == rec.appraiser_id.user_id and rec.state not  in ['done', 'close']:
                rec.can_emp_edit = True
            if rec.state == 'new':
                rec.can_emp_edit = True

    @api.depends('appraiser_id')
    def compute_user_edit(self):
        for rec in self:
            rec.can_edit = False
            if rec.env.user == rec.appraiser_id.user_id or self.env.user.has_group('hr.group_hr_user'):
                rec.can_edit = True

    @api.depends('appraiser_id')
    def compute_user_see(self):
        for rec in self:
            rec.can_see = False
            if rec.state in ['done', 'close']:
                rec.can_see = True
                return
            if rec.env.user == rec.appraiser_id.user_id:
                rec.can_see = True


class HrAppraisalLine(models.Model):
    _name = "hr.appraisal.line"
    _rec_name = 'evaluation_id'

    type = fields.Selection(string='Type', selection=[
        ('objective', 'Objective'),
        ('competencies', 'competencies'), ], required=True, )

    employee_id = fields.Many2one(comodel_name='hr.employee', )
    annual_appraisal_id = fields.Many2one(comodel_name='hr.appraisal.appraisal', )
    annual_state = fields.Selection(related="annual_appraisal_id.state")
    competencies_appraisal_id = fields.Many2one(comodel_name='hr.appraisal.appraisal', )
    competencies_state = fields.Selection(related="competencies_appraisal_id.state")
    annual_appraisal_tmp_id = fields.Many2one(related="annual_appraisal_id.appraisal_tmp_id")
    competencies_appraisal_tmp_id = fields.Many2one(related="competencies_appraisal_id.appraisal_tmp_id")
    appraisal_weight_ids = fields.Many2many('appraisal.weight', related='annual_appraisal_tmp_id.appraisal_weight_ids')
    competencies_weight_ids = fields.Many2many('appraisal.weight',
                                               related='competencies_appraisal_tmp_id.appraisal_weight_ids')
    # evaluation_id = fields.Many2one(comodel_name='hr.appraisal.evaluation.scale', )
    evaluation = fields.Char('Evaluation')
    evaluation_id = fields.Many2one('hr.appraisal.evaluation')
    weight_id = fields.Many2one('appraisal.weight', string="weight", required=1)
    emp_score = fields.Selection(string='Employee Score', selection=[
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5')])
    initial_score = fields.Selection(string='Initial Score', selection=[
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5')])
    manager_score = fields.Selection(string='Manager Score', selection=[
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5')])
    accept = fields.Boolean(default=True)
    final_score = fields.Float(string="Final Score %", compute="get_final_score")
    note = fields.Text('Note')
    history_ids = fields.One2many(comodel_name='hr.appraisal.history', inverse_name='appraisal_line_id')
    last_history_id = fields.Many2one('hr.appraisal.history')
    
    
    def get_portal_url(self):
        if self:
            portal_url = self[0].get_base_url()
        else:
            portal_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        # portal_link = "%s/?db=%s" % (portal_url, self.env.cr.dbname)
        portal_link = "%s/update/appraisal/id=%s" % (portal_url, self.id)
        print("XXXXXXXXXXXX123XXXXXXXXX ", portal_link)
        return portal_link
    
    
    def action_edit(self):
        view_id = self.env.ref('plustech_hr_appraisal.appraisal_history_view_form').id
        return {
            'name': 'Edit APPRAISAL',
            'view_type': 'form',
            'views': [(view_id, 'form')],
            'res_model': 'hr.appraisal.history',
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_appraisal_line_id': self.id,
                'default_type': self.type,
                'default_old_weight_id': self.weight_id.id,
                'default_old_evaluation_id': self.evaluation_id.id,
                'default_employee_id': self.annual_appraisal_id.employee_id.id if self.annual_appraisal_id else self.competencies_appraisal_id.employee_id.id,
                'default_appraisal_weight_ids': [(6, 0, self.annual_appraisal_tmp_id.appraisal_weight_ids.ids)],
                'default_competencies_weight_ids': [(6, 0, self.competencies_appraisal_tmp_id.appraisal_weight_ids.ids)],
            },
        }

    def action_view_history(self):
        action = self.env.ref("plustech_hr_appraisal.appraisal_history_action").sudo().read()[0]
        action["domain"] = [("id", "in", self.history_ids.ids)]
        action["target"] = 'new'
        return action

    @api.depends('manager_score', 'weight_id')
    def get_final_score(self):
        for rec in self:
            rec.final_score = 0
            if rec.manager_score and rec.weight_id:
                rec.final_score = (float(rec.weight_id.weight) / 100 * (((int(rec.manager_score) * 2) + 2)) / 10) * 100

    # @api.constrains('evaluation_id' , 'rate')
    # def constrains_rate(self):
    #     for rec in self:
    #         if rec.evaluation_id.rate_to < rec.rate:
    #             raise UserError(_("Rate from must be less than Evaluation rate to"))
    #         if  rec.rate < rec.evaluation_id.rate_from:
    #             raise UserError(_("Rate from must be Bigger than Evaluation rate from"))


class HrAppraisalHistory(models.Model):
    _name = "hr.appraisal.history"

    appraisal_line_id = fields.Many2one(comodel_name='hr.appraisal.line')
    employee_id = fields.Many2one(comodel_name='hr.employee', readonly=1)
    change_weight = fields.Boolean('Change Weight?')
    old_evaluation_id = fields.Many2one('hr.appraisal.evaluation')
    new_evaluation_id = fields.Many2one('hr.appraisal.evaluation')
    old_weight_id = fields.Many2one('appraisal.weight', string="Old Weight", readonly=1)
    new_weight_id = fields.Many2one('appraisal.weight', string="weight")
    appraisal_weight_ids = fields.Many2many('appraisal.weight', readonly=1)
    competencies_weight_ids = fields.Many2many('appraisal.weight', 'appraisal_competencies_rel', readonly=1)
    note = fields.Text('Note')

    type = fields.Selection(string='Type', selection=[
        ('objective', 'Objective'),
        ('competencies', 'competencies'), ], required=True, )
    
    @api.onchange('change_weight')
    def _onchange_change_weight(self):
        if self.change_weight:
            self.new_evaluation_id = self.old_evaluation_id
        else:
            self.new_evaluation_id = False


    @api.onchange('new_evaluation_id', 'appraisal_weight_ids', 'competencies_weight_ids','change_weight')
    def change_lines_get_eval(self):
        for rec in self:
            evaluation_ids = self.env['hr.appraisal.evaluation']
            if rec.appraisal_line_id.annual_appraisal_id:
                if rec.change_weight:
                    evaluation_ids = self.env['hr.appraisal.evaluation'].search([
                        ('employee_id', '=', rec.employee_id.id),
                        ('type', '=', 'objective'),
                    ])
                else:
                    evaluation_ids = self.env['hr.appraisal.evaluation'].search([
                        ('employee_id', '=', rec.employee_id.id),
                        ('type', '=', 'objective'),
                        ('id', 'not in', rec.appraisal_line_id.annual_appraisal_id.annual_ids.mapped('evaluation_id').ids),
                    ])
            if rec.appraisal_line_id.competencies_appraisal_id:
                if rec.change_weight:
                    evaluation_ids = self.env['hr.appraisal.evaluation'].search([
                        ('employee_id', '=', rec.employee_id.id),
                        ('type', '=', 'competencies'),
                    ])
                else:
                    evaluation_ids = rec.env['hr.appraisal.evaluation'].search([
                        ('employee_id', '=', rec.employee_id.id),
                        ('type', '=', 'competencies'),
                        ('id', 'not in', rec.appraisal_line_id.competencies_appraisal_id.competencies_ids.mapped('evaluation_id').ids),
                    ])
            return {'domain': {'new_evaluation_id': [('id','in',evaluation_ids.ids)]}}


    def save_edit(self):
        for line in self.appraisal_line_id:
            line.evaluation_id = self.new_evaluation_id
            # Todo:
            # if line.annual_appraisal_id:
            #     weights = sum(float(x.weight_id.weight) for x in line.annual_appraisal_id.annual_ids.filtered(lambda m: m.id != line.id))
            #     if (weights + float(self.new_weight_id.weight)) != line.annual_appraisal_id.objectives_percentage:
            #         raise  UserError(_('Annual Weight Must equal to %s')%line.annual_appraisal_id.objectives_percentage)
            line.weight_id = self.new_weight_id.id
            # line.annual_appraisal_id.constrains_lines()
            name = ''
            main_line = self.env['hr.appraisal.appraisal']
            if self.appraisal_line_id.annual_appraisal_id:
                self.appraisal_line_id.annual_appraisal_id.state = 'edit'
                name = self.appraisal_line_id.annual_appraisal_id.employee_id.name
                main_line = self.appraisal_line_id.annual_appraisal_id
            if self.appraisal_line_id.competencies_appraisal_id:
                self.appraisal_line_id.competencies_appraisal_id.state = 'edit'
                name = self.appraisal_line_id.competencies_appraisal_id.employee_id.name
                main_line = self.appraisal_line_id.competencies_appraisal_id

            message = _("Appraisal Edit For Employee %s") % (name)
            recipient_partners = []
            group_id = self.env.ref('hr.group_hr_user').id
            user_ids = self.env['res.users'].search([('groups_id', '=', group_id)])
            for user in user_ids:
                if user.partner_id:
                    recipient_partners.append(user.partner_id.id)
                    vals = {
                        'subject': "Appraisal Notification",
                        'body': message,
                        'res_id': main_line.id,
                        'model': 'hr.appraisal.appraisal',
                        'message_type': 'notification',
                        'partner_ids': [(4, user.partner_id.id)]
                    }
                    message_ids = self.env['mail.message'].create(vals)
                    self.env['mail.notification'].create(
                        {'mail_message_id': message_ids.id, 'res_partner_id': user.partner_id.id})
            line.accept = False
            if not line.last_history_id:
                line.last_history_id = self.id


class HrAppraisalEvaluation(models.Model):
    _name = "hr.appraisal.evaluation"

    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    employee_id = fields.Many2one('hr.employee')
    name = fields.Char()
    type = fields.Selection(string='Type', selection=[
        ('objective', 'Objective'),
        ('competencies', 'competencies'), ], required=True, )
