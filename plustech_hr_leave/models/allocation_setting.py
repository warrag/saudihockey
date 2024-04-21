# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    days_per_year = fields.Integer(string='Number of days per Year ', default=360)


class ConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'


    days_per_year = fields.Integer(string='Number of days per year',related='company_id.days_per_year',readonly=False)
