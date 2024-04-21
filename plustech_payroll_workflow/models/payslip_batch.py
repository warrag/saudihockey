# -*- coding:utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    stage_id = fields.Many2one('payslip.run.stage', 'Target Stage', ondelete='restrict', tracking=True)
    generate_entry = fields.Boolean(string='Create Journal Entry', related='stage_id.generate_entry')
    post_entry = fields.Boolean(string='Post Journal Entry', related='stage_id.post_entry')
    payment = fields.Boolean(string='Register Payment', related='stage_id.payment')
    cancel = fields.Boolean('Cancel Batch', related='stage_id.cancel')
    set_to_draft = fields.Boolean(string='Set To Draft', related='stage_id.set_to_draft')
    backward = fields.Boolean(string='Backward', related='stage_id.backward')
    show_for_current_user = fields.Boolean(string='Show For Current User', compute='_compute_show_for_current_user')
    next_stage_id = fields.Many2one('payslip.run.stage', compute='compute_next_stage')
    approval_status_ids = fields.One2many('hr.payroll.approval.status', 'batch_id')

    def _compute_show_for_current_user(self):
        self.show_for_current_user = False
        if self.env.user.id in self.stage_id.user_ids.ids:
            self.show_for_current_user = True

    def action_forward(self):
        if self.generate_entry and self.state != 'close':
            raise ValidationError(_("Please Create Batch Entry before forward!"))
        if self.post_entry and self.state != 'post':
            raise ValidationError(_("Please Post Batch Entry before forward!"))
        next_stage_id = self.stage_id.sequence + 1
        next_stage = self.env['payslip.run.stage'].search([('sequence', '=', next_stage_id)])
        self.write({
            'approval_status_ids': [(0, 0, {'user_id': self.env.user.id, 'action': 'Approved',
                                     'action_date': fields.Date().today(),
                                            'batch_id': self.id, 'stage_id':  self.stage_id.id})],
        })
        if next_stage:
            self.write({'stage_id': next_stage.id})

    def action_backward(self):
        previous_stage_id = self.stage_id.sequence - 1
        previous_stage = self.env['payslip.run.stage'].search([('sequence', '=', previous_stage_id)])
        self.write({
            'approval_status_ids': [(0, 0, {'user_id': self.env.user.id, 'action': 'Rejected',
                                            'action_date': fields.Date().today(),
                                            'stage_id': self.stage_id.id, 'batch_id': self.id})],
        })
        if previous_stage:
            self.write({'stage_id': previous_stage.id})

    @api.depends('stage_id')
    def compute_next_stage(self):
        for record in self:
            next_stage_id = self.stage_id.sequence + 1
            next_stage = self.env['payslip.run.stage'].search([('sequence', '=', next_stage_id)])
            record.next_stage_id = next_stage.id

    @api.model
    def default_get(self, fields):
        res = super(HrPayslipRun, self).default_get(fields)
        stages = self.env['payslip.run.stage'].search([])
        if stages:
            default_stage = stages.filtered(lambda stage: stage.sequence == min(stages.mapped('sequence')))
            res.update({
                'stage_id': default_stage[0].id,
            })
        return res

