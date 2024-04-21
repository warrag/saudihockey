from datetime import datetime
import string
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class TrainingActivity(models.Model):
    _name = 'training.training.activity'

    activity_type_id = fields.Many2one('mail.activity.type', string='Activity Type', required=True)
    users_id = fields.Many2one('res.users', string='Users')
    note = fields.Char('Note', required=True)
    subject = fields.Char('Subject')
    training_state = fields.Selection(selection=[('new', 'New'), ('direct_manager', 'Waiting Manager Approval'),
                                                 ('officer', 'Waiting Human Resource Officer Approval'),
                                                 ('hr', 'Waiting Human Resource Report'),
                                                 ('admin', 'Financial and Administrative Affairs Approval'),
                                                 ('ceo', 'Waiting CEO Approval'), ('approve', 'Approved'),
                                                 ('close', 'Closed'), ('cancel', 'Canceled')], default='new')
