# -*- coding: utf-8 -*-

from odoo import models,fields


class BusinessTrip(models.Model):
    _inherit = 'hr.deputation'

    training_request_id = fields.Many2one('training.training')
