from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class RecruitmentPlan(models.Model):
    _name = 'recruitment.plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Recruitment Plan'

    @api.model
    def _get_default_department(self):
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)])
        department = self.env['hr.department'].search([('id', '=', employee.department_id.id)])
        return department

    name = fields.Char()
    department_id = fields.Many2one('hr.department', string='Department Name', default=_get_default_department)
    stage_id = fields.Many2one('hr.approval.stage', string='Stage', tracking=True, readonly=True,
                               domain=[('approval_type_id.model_name', '=', 'recruitment.plan')])
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.user.company_id.id)
    request_date = fields.Date(string='Request Date', default=fields.Date.today())
    attachment_number = fields.Integer('Number of Attachments', compute='get_attachment_ids')
    first_stage = fields.Boolean(compute="_compute_stage")
    is_last_stage = fields.Boolean(compute="_compute_stage")
    plan_line_ids = fields.One2many('recruitment.plan.line', 'plan_id', string='Plan lines',
                                    copy=False,)

    @api.depends('stage_id')
    def _compute_stage(self):
        is_last_stage = True
        stages = self.env['hr.approval.stage'].search([('approval_type_id.model_name', '=', 'recruitment.plan')])
        if stages:
            next_stage = stages.filtered(lambda stage: stage.sequence == max(stages.mapped('sequence')))
            if next_stage == self.stage_id:
                is_last_stage = True
            else:
                is_last_stage = False
        if self.stage_id.is_default:
            self.first_stage = True
        else:
            self.first_stage = False
        self.is_last_stage = is_last_stage

    @api.model
    def default_get(self, fields):
        res = super(RecruitmentPlan, self).default_get(fields)
        default_stage = self.env['hr.approval.stage'].search([('is_default', '=', True),
                                                              (
                                                                  'approval_type_id.model_name', '=',
                                                                  'recruitment.plan')])
        res.update({
            'stage_id': default_stage.id,
        })
        return res

    def action_approve(self):
        next_stage = self.stage_id.sequence + 1
        next_stage = self.env['hr.approval.stage'].search([('approval_type_id.model_name', '=', 'recruitment.plan'),
                                                           ('sequence', '=', next_stage)])
        if next_stage:
            self.stage_id = next_stage.id or False
        users = next_stage.mapped('approval_ids').mapped('user_id')
        self._create_activity(users)
        self.sudo()._get_user_approval_activities(user=self.env.user).action_feedback()

    def action_submit(self):
        stages = self.env['hr.approval.stage'].search([('approval_type_id.model_name', '=', 'recruitment.plan'),
                                                       ('id', '!=', self.stage_id.id)])
        next_stage = stages.filtered(lambda stage: stage.sequence == min(stages.mapped('sequence')))
        self.stage_id = next_stage.id or False
        users = next_stage.mapped('approval_ids').mapped('user_id')
        self._create_activity(users)
        self.sudo()._get_user_approval_activities(user=self.env.user).action_feedback()

    def _create_activity(self, users):
        for user in users:
            self.activity_schedule(
                'plustech_hr_approvals.mail_activity_data_hr_approval',
                user_id=user.id)

    def _get_user_approval_activities(self, user):
        domain = [
            ('res_model', '=', 'recruitment.plan'),
            ('res_id', 'in', self.ids),
            ('activity_type_id', '=', self.env.ref('plustech_hr_approvals.mail_activity_data_hr_approval').id),
            ('user_id', '=', user.id)
        ]
        activities = self.env['mail.activity'].search(domain)
        return activities

    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        res['domain'] = [('res_model', '=', 'recruitment.plan'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'recruitment.plan', 'default_res_id': self.id}
        return res

    def get_attachment_ids(self):
        for rec in self:
            rec.attachment_number = self.env['ir.attachment'].search_count([('res_model', '=', 'recruitment.plan'),
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
                'recruitment.plan', sequence_date=seq_date) or _('New')
        result = super(RecruitmentPlan, self).create(vals)
        return result

    def unlink(self):
        for record in self:
            if not record.first_stage:
                raise ValidationError(_("You can't delete record not in draft stage"))
        res = super(RecruitmentPlan, self).unlink()
        return res


class RecruitmentPlanLine(models.Model):
    _name = 'recruitment.plan.line'

    plan_id = fields.Many2one('recruitment.plan', string='Recruitment Plan',
                              index=True, required=True, readonly=True, auto_join=True, ondelete="cascade",
                              check_company=True,
                              )
    sequence = fields.Char(string='No#')
    job_position_id = fields.Many2one('hr.job', string='Job Position',
                                      domain="[('id','not in', existing_positions_ids)]")
    degree_id = fields.Many2one('hr.recruitment.degree', string='Degree')
    skill_ids = fields.Many2many('hr.employee.skill', string='Skills')
    knowledge = fields.Text(string='Knowledge')
    work_type = fields.Selection([('full', 'Full Time'), ('part', 'Part Time')],
                                 string='Work Type')
    demand = fields.Integer(string='Demand')
    current_employees = fields.Integer(string='Current Employees', compute='compute_current_employees')
    open_positions = fields.Integer(string='Open Position')
    other_requirements = fields.Text(string='Other Requirements')
    existing_positions_ids = fields.Many2many('hr.job', compute='_compute_existing_positions_ids')

    @api.depends('plan_id')
    def _compute_existing_positions_ids(self):
        for record in self:
            record.existing_positions_ids = record.plan_id.plan_line_ids.job_position_id

    @api.depends('job_position_id')
    def compute_current_employees(self):
        for record in self:
            employees = 0
            if self.job_position_id:
                employees = self.env['hr.employee'].search_count([('job_id', '=', record.job_position_id.id)])
            record.current_employees = employees

    @api.model
    def default_get(self, fields):
        res = {}
        context = self.env.context
        if context:
            context_keys = context.keys()
            next_sequence = 1
            if 'plan_line_ids' in context_keys:
                if len(context.get('plan_line_ids')) > 0:
                    next_sequence = len(context.get('plan_line_ids')) + 1
        res.update({'sequence': next_sequence})
        return res

