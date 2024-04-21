# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PayslipBatchStage(models.Model):
    _name = 'payslip.run.stage'
    _description = 'Payslip run Stage'
    _order = 'sequence, id'

    active = fields.Boolean(default=True)
    name = fields.Char(required=True, translate=True)
    description = fields.Text(translate=True)
    sequence = fields.Integer('Sequence', default=10)
    user_ids = fields.Many2many(
        'res.users', relation='user_stage_rel', string="Approvers")
    generate_entry = fields.Boolean(string='Create Journal Entry')
    post_entry = fields.Boolean(string='Post Journal Entry')
    payment = fields.Boolean(string='Register Payment')
    cancel = fields.Boolean('Cancel Batch')
    set_to_draft = fields.Boolean(string='Set To Draft')
    backward = fields.Boolean(string='Backward')
    print = fields.Boolean(string='Print in Report')
