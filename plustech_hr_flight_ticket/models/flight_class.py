# -*- coding: utf-8 -*-

from datetime import datetime
import string
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class HrFlightClass(models.Model):
    _name = 'flight.class'

    name = fields.Char(translate=True, required=True)
    partner_id = fields.Many2one('res.partner', string='Airline', domain="[('is_airline','=',True)]", required=True)