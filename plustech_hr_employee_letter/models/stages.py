# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class LetterStages(models.Model):
    _name = 'letter.stages'
    _description = 'Letters Stages'
    _rec_name = 'name'
    _order = 'sequence, id'

    sequence = fields.Integer(default=1)
    name = fields.Char(string='Stage Name',required=True)
    next_stage = fields.Many2one(comodel_name='letter.stages', string='Next Stage',)
    group_ids = fields.Many2many(comodel_name='res.groups', string='Groups')
    default_stage = fields.Boolean(string='Is Default Stage')
    cancel_stage = fields.Boolean(string='Is cancel stage')
    sent_notification = fields.Boolean(string='Sent Notification')
    print = fields.Boolean('Print')
    readonly = fields.Boolean('Readonly')
    activity_type_id = fields.Many2one('mail.activity.type', string='Activity Type')

    @api.constrains('default_stage')
    def _check_unique_code(self):
        for line in self:
            lines = self.env['letter.stages'].search([('id', '!=', line.id), ('default_stage', '=', True)])
            if len(lines) > 0 and self.default_stage:
                raise ValidationError(_('There is default stage already defined!'))
