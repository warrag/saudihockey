# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class HrFlightTicket(models.Model):
    _inherit = 'hr.flight.ticket'

    deputation_id = fields.Many2one('hr.deputation', string='Business Trip')

