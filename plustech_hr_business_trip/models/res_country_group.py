# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class CountryGroup(models.Model):
    _inherit = 'res.country.group'

    days_before = fields.Integer(string='Days Before')
    days_after = fields.Integer(string='Days After')
    extra_days = fields.Integer(string="Extra Days", compute='compute_extra_days')
    code = fields.Char(string='Code')

    @api.depends('days_before', 'days_after')
    def compute_extra_days(self):
        for record in self:
            record.extra_days = record.days_before + record.days_after
    
    @api.constrains('business_trip', 'country_ids')
    def _check_duplicate(self):
        for record in self:
            for country_id in record.country_ids:
                if len(country_id.country_group_ids) > 1:
                    raise ValidationError(_('Duplicate Country Group for %s') % country_id.name)


class Country(models.Model):
    _inherit = 'res.country'

    country_group_id = fields.Many2one('res.country.group')

