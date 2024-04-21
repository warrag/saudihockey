# -*- coding: utf-8 -*-
import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class LetterRequest(models.Model):
    _name = 'letter.request'
    _description = 'Letter Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def get_letter_field_value(self, technical_name):
        field = self.field_ids.filtered(lambda line: line.field_id.technical_name == technical_name)
        value = field[0].field_value if field else ""
        return value

    name = fields.Char(string='Subject')
    request_date = fields.Date(default=fields.Date.today())
    letter_type_id = fields.Many2one('letter.letter', copy=False)
    request_id = fields.Many2one('hr.employee', 'Requester', default=lambda self: self.env.user.employee_id)
    contract_id = fields.Many2one(related='request_id.contract_id', strore=True)
    note = fields.Text()
    state = fields.Selection(selection=[('draft', 'Draft'),
                                        ('in_progress', 'In Progress'),
                                        ('cancel', 'Cancelled'),
                                        ('refuse', 'Refused'),
                                        ('done', 'Done')
                                        ], default='draft')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)
    stage_id = fields.Many2one(comodel_name='letter.temp.stage',string='Stage',tracking=True,copy=False)
    can_print = fields.Boolean(compute="_compute_print")
    readonly = fields.Boolean('Readonly', compute="_compute_readonly")
    stages_ids = fields.Many2many(comodel_name='letter.temp.stage', string='Stages', compute="_compute_stages")
    history_ids = fields.One2many('letter.request.history', 'request_id')
    field_ids = fields.One2many('letter.fields.line', 'letter_id')
    need_approval = fields.Boolean(string='Need Approval', related="letter_type_id.need_approval")
    approve_boolean = fields.Boolean(string="Approve Stage",compute="_compute_approve_stage_id")
    submit_boolean = fields.Boolean(string="Submit Stage",compute="_compute_submit_stage_id")
    to_refuse = fields.Boolean(string="to_refuse",compute="_compute_to_refuse")
    last_stage = fields.Boolean(string='Is Last Stage', compute="_compute_last_stage_id")
    approval_ids = fields.One2many('letter.approval', 'letter_id')
    latter_content = fields.Html(string='Letter Content')
    has_access = fields.Boolean(string="Who Can Access Process Btn", compute="_compute_who_access_btn_process")
    last_stg = fields.Boolean(string="Last stage", copy=False)

    @api.depends('stage_id')
    def _compute_readonly(self):
        for record in self:
            if record.need_approval and  record.stage_id.readonly:
                record.readonly = True
            else:
                record.readonly = False

    @api.depends('stage_id', 'need_approval')
    def _compute_print(self):
        for record in self:
            if not record.need_approval or record.stage_id.print:
                record.can_print = True
            else:
                record.can_print = False

    @api.depends('letter_type_id')
    def _compute_stages(self):
        for rec in self:
            rec.stages_ids = False
            if rec.letter_type_id:
                if rec.letter_type_id.stage_ids:
                    rec.stages_ids = [(6, 0, rec.letter_type_id.stage_ids.ids)]
                    if not rec.stage_id:
                        rec.stage_id = rec.letter_type_id.stage_ids.sudo().search([], order='sequence ASC')[0].id
            else:
                rec.stage_id = False

    @api.depends('letter_type_id', 'stage_id')
    def _compute_who_access_btn_process(self):
        for record in self:
            record.has_access = False
            stage = self.history_ids.filtered(lambda line: line.stage_id == record.stage_id)
            if stage and self.env.user.id in stage.user_ids.ids:
                record.has_access = True

    def action_process(self):
        for record in self:
            stages = record.history_ids.filtered(lambda line: line.stage_id == record.stage_id).stage_id
            if stages:
                self._action_feedback_activity(stages[0].stage_id.id)
            stage_tmp_ids = record.letter_type_id.stage_ids
            curr_stage_id = record.stage_id
            for stage in curr_stage_id:
                index = stage_tmp_ids.sudo().search([], order='sequence ASC').mapped('sequence').index(stage.sequence)
                if (index + 1) < len(stage_tmp_ids.sudo().search([], order='sequence ASC').mapped('sequence')):
                    # print(index, "index ",rec.letter_type_id.stage_ids.mapped('sequence')[index+1])
                    if not record.letter_type_id.stage_ids.mapped('sequence')[-1] == index:
                        next_stage_id = record.letter_type_id.stage_ids.search([
                            ('letter_id', '=', record.letter_type_id.id),
                            ('sequence', '=', record.letter_type_id.stage_ids.mapped('sequence')[index + 1])])
                        approval_stage = self.history_ids.filtered(lambda line: line.stage_id == record.stage_id)
                        if len(approval_stage) != 0:
                            approval_stage[0].write({
                                'user_id': self.env.user,
                                'date': datetime.datetime.now(),
                                'state': 'done'
                            })

                        self.write({'stage_id': next_stage_id.id,
                                    'state': 'in_progress'})
                        if next_stage_id and next_stage_id.sent_notification:
                            self._create_activity(next_stage_id)
                if len(record.letter_type_id.stage_ids) == stage.sequence:
                    record.write({'last_stg': True, 'state': 'done'})
                    approval_stage = self.history_ids.filtered(lambda line: line.stage_id == record.stage_id)
                    if len(approval_stage) != 0:
                        approval_stage[0].write({
                            'user_id': self.env.user,
                            'date': datetime.datetime.now(),
                            'state': 'done'
                        })

    def _create_activity(self, stage):
        stages = self.history_ids.filtered(lambda line: line.stage_id == stage)
        if stage.activity_type_id and stages:
            for user in stages[0].user_ids:
                self.env['mail.activity'].sudo().create({
                    'activity_type_id': stage.activity_type_id.id,
                    'res_id': self.id,
                    'res_model_id': self.env['ir.model'].sudo().search([('model', '=', 'letter.request')], limit=1).id,
                    'icon': 'fa-pencil-square-o',
                    'date_deadline': fields.Date.today(),
                    'user_id': user.id,
                    'summary': 'Letter Approve',
                    'note': 'Letter approval request by %s' % self.env.user.name,
                })

    def _action_feedback_activity(self, stage_id):
        for record in self:
            previous_letter_activity = self.env['letter.temp.stage'].sudo().search([('stage_id', '=', stage_id)])
            for activity in previous_letter_activity:
                self.sudo()._get_user_approval_activities(user=self.env.user,
                                                          activity_type=activity.activity_type_id,
                                                          record=record).action_feedback()

    def _get_user_approval_activities(self, user=False, activity_type=False, record=False):
        domain = [
            ('res_model', '=', 'letter.request'),
            ('res_id', 'in', record.ids),
            ('activity_type_id', '=', activity_type.id)]
        activities = self.env['mail.activity'].search(domain)
        return activities
    
    def get_render_template(self):
        if not self.letter_type_id:
            raise UserError(_("Please Select letter print template"))
        rendered_content = self.env['letter.letter'].render_template(
            self.letter_type_id.body,
            self.letter_type_id.model_id.model,
            self._origin.id)
        return rendered_content

    @api.onchange('letter_type_id', 'request_id')
    def _onchange_letter_type_id(self):
        self.field_ids = None
        self.history_ids = None
        if self.letter_type_id:
            self.latter_content = self.sudo().get_render_template()
            self.name = self.letter_type_id.name
            field_ids = []
            for field in self.letter_type_id.field_ids:
                result = {'field_id': field.id, 'field_value': field.default_value}
                field_ids.append((0, 0, result))
            history_ids = []
            for stage in self.letter_type_id.stage_ids:
                user_ids = stage.user_ids
                if stage.approval == 'employee':
                    user_ids = self.request_id.user_id
                elif stage.approval == 'direct_mg':
                    user_ids = self.request_id.parent_id.user_id
                vals = {
                    'request_id': self.id,
                    'stage_id': stage.id,
                    'approval': stage.approval,
                    'user_ids': user_ids
                }
                history_ids.append((0, 0, vals))
            self.update({
                'history_ids': history_ids,
                'field_ids': field_ids
            })

    @api.depends('stage_id')
    def _compute_last_stage_id(self):
        if self:
            for rec in self:
                rec.last_stage = False
                last_stage = self.env['letter.temp.stage'].search([('sequence', '!=', False)], order='sequence desc',limit=1)
                if last_stage:
                    rec.last_stage = True
                else:
                    rec.last_stage = False

    @api.depends('stage_id')
    def _compute_approve_stage_id(self):
        if self:
            for rec in self:
                rec.approve_boolean = False
                if rec.stage_id.user_ids:
                    for user in rec.stage_id.user_ids:
                        if self.env.user.id == user.id:
                            rec.approve_boolean = True
                else:
                    rec.approve_boolean = False

    @api.depends('stage_id')
    def _compute_submit_stage_id(self):
        if self:
            for rec in self:
                rec.submit_boolean = False
                if rec.stage_id.user_ids:
                    for user in rec.stage_id.user_ids:
                        if user.id == self.env.user.id:
                            rec.submit_boolean = True
                else:
                    rec.submit_boolean = False

    @api.depends('stage_id')
    def _compute_to_refuse(self):
        if self:
            for record in self:
                record.to_refuse = False
                refuse_stage = self.env['letter.temp.stage'].search([('cancel_stage', '=', True),
                                                                          ('id', '=', record.stage_id.id)])
                stage = self.history_ids.filtered(lambda line: line.stage_id == record.stage_id)
                if self.stage_id.id in refuse_stage.ids and record.state == 'in_progress':
                    if self.env.user.id in stage.user_ids.ids:
                        record.to_refuse = True
                else:
                    record.to_refuse = False

    def action_draft(self):
        default_stage = self.env['letter.temp.stage'].search([('default_stage', '=', True)])
        self.write({'stage_id': default_stage.id, 'state': 'draft'})

    def action_refuse(self):
        refuse_stage = self.history_ids.filtered(lambda line: line.stage_id == self.stage_id)
        if len(refuse_stage) != 0:
            refuse_stage[0].write({
                'user_id': self.env.user,
                'date': datetime.datetime.now(),
                'state': 'refuse'
            })
            self.write({'state': 'refuse'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def print_letter(self):
        return self.env.ref(self.letter_type_id.report_xml_id).report_action(self)

    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise ValidationError(_("You can't delete record not in draft state"))
        res = super(LetterRequest, self).unlink()
        return res



class LettersApproval(models.Model):
    _name = 'letter.approval'

    user_id = fields.Many2one('res.users', string='Approval')
    approval_date = fields.Date(string='Approval Date')
    action = fields.Char(string='Action')
    letter_id = fields.Many2one('letter.request')


class LettersHistory(models.Model):
    _name = 'letter.request.history'

    request_id = fields.Many2one(comodel_name='letter.request', string='Request')
    stage_id = fields.Many2one(comodel_name='letter.temp.stage', string='Stage', required=True)
    appear_on_report = fields.Boolean('Appear On Report', related="stage_id.appear_on_report")
    date = fields.Datetime(string="Operation Date")
    state = fields.Selection([('waiting', 'Waiting'), ('done', 'Done'), ('refuse', 'Refused')],
                             default='waiting', string='Status')
    user_id = fields.Many2one('res.users', string='Approved By')
    user_ids = fields.Many2many('res.users', string='Users')
    approval = fields.Selection(string='', selection=[
        ('employee', 'Employee'),
        ('direct_mg', 'Direct Manager'),
        ('depart_mg', 'Department Manager'),
        ('hr_officer', 'HR Officer'),
        ('hr_Manager', 'HR Manager'),
        ('financial', 'Financial'),
        ('ceo', 'CEO'),
    ], required=True, )


class LetterFieldsLine(models.Model):
    _name = 'letter.fields.line'

    field_id = fields.Many2one('hr.letter.fields', string='Field Name')
    field_value = fields.Char(string='Value',translate=True)
    letter_id = fields.Many2one('letter.request')
    required = fields.Boolean(related='field_id.required')
    visible = fields.Boolean(related="field_id.visible", string='Visible', readonly=False)

