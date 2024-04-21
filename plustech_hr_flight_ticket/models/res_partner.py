# -*- coding: utf-8 -*-

from datetime import datetime
import string
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ResParntner(models.Model):
    _inherit = 'res.partner'

    is_airline = fields.Boolean('Is Airline')