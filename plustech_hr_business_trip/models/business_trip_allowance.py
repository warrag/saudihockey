# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class HRDeputationAllowance(models.Model):
    _name = 'hr.deputation.allowance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Deputation Allowance'
    _check_company_auto = True

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'The code of the Allowance must be unique!')
    ]

    name = fields.Char(string='name', translate=True)
    code = fields.Char(string='Code')
    amount = fields.Float(string='Per-diem Amount')
    type = fields.Selection([('fixed', 'Fixed Amount'), ('percentage', 'Percentage')])
    active = fields.Boolean(string='Active', default=True)
    product_id = fields.Many2one('product.product', string='Allowance Product', domain=[('detailed_type', '=', 'service')])
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)


class HRDeputationCities(models.Model):
    _name = 'deputation.cities.allowance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Deputation Cities Allowance'

    def name_get(self):
        res = []
        for record in self:
            name = record.name or '/'
            if record.country_group_id:
                name = name + " - " + record.country_group_id.name
            res.append((record.id, name))
        return res

    name = fields.Char(string='Name')
    from_city_id = fields.Many2one('res.city', string='From City',
                                   domain="[('country_id', '=', country_id)]")
    to_city_id = fields.Many2one('res.city', string='To City', domain="[('id', '!=', from_city_id)]")
    amount = fields.Float(string='Per-diem Allowance')
    deputation_type = fields.Selection([('internal', 'Internal'), ('external', 'External')], default='internal',
                                       required=True)
    country_id = fields.Many2one('res.country', string='From Country',
                                 default=lambda self: self.env.company.country_id)
    dest_country_id = fields.Many2one('res.country', string='Destination Country')
    by_company_allowance = fields.Float(string='By Company')
    by_employee_allowance = fields.Float(string='By Employee')
    without_overnight_allowance = fields.Float(string='Without Overnight')
    country_group_id = fields.Many2one('res.country.group', string='Country Group')
    days_before = fields.Integer(string='Days Before')
    days_after = fields.Integer(string='Days After')
    count_allowance = fields.Integer(compute='_count_allowance')
    active = fields.Boolean(string='Active', default=True)
    allowance_ids = fields.One2many('deputation.cities.allowance.line', 'parent_id')
    country_ids = fields.Many2many('res.country')
    excluded_city_ids = fields.Many2many('res.city', string='Excluded Cities', domain="[('country_id', 'in', country_ids)]")

    @api.model
    def create(self, vals):
        if vals.get('name', _('/')) == _('/'):
            seq_date = None
            if 'request_date' in vals:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['request_date']))
            vals['name'] = self.env['ir.sequence'].next_by_code('deputation.allowance', sequence_date=seq_date) or _('/')
        result = super(HRDeputationCities, self).create(vals)
        return result

    # @api.depends('to_city_id')
    # def _get_country_group_id(self):
    #     for record in self:
    #         country_group_id = self.env['res.country.group'].search(
    #             [('country_ids', '=', record.to_city_id.country_id.id)], limit=1)
    #         record.country_group_id = country_group_id

    @api.onchange('country_group_id')
    def _onchange_country_group(self):
        self.days_before = self.country_group_id.days_before
        self.days_after = self.country_group_id.days_after
        self.country_ids = self.country_group_id.country_ids.ids

    def _count_allowance(self):
        for record in self:
            record.count_allowance = len(record.allowance_ids)

    # @api.onchange('dest_country_id', 'from_city_id')
    # def _onchange_dest_country_id(self):
    #     domain = [('country_id', '=', self.dest_country_id.id)] if self.dest_country_id and \
    #                                                                self.deputation_type == 'external' else [
    #         ('country_id', '=', self.country_id.id), ('id', '!=', self.from_city_id.id)]
    #     return {'domain': {'to_city_id': domain}}

    def action_view_allowance(self):
        return {
            'name': _('Allowance'),
            'view_mode': 'tree',
            'res_model': 'deputation.cities.allowance.line',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('plustech_hr_business_trip.deputation_cities_allowance_lines_view_tree').id,
            'context': {'default_parent_id': self.id},
            'domain': [('parent_id', '=', self.id)]
        }


class CitiesAllowanceLines(models.Model):
    _name = 'deputation.cities.allowance.line'
    _description = 'Cities Allowance Lines'

    job_position_ids = fields.Many2many('hr.job', string='Job Position')
    per_diem_amount = fields.Float(string='Per-diem Amount')
    internal_per_diem = fields.Float(string='Internal Per-diem Amount')
    external_per_diem = fields.Float(string='External Per-diem Amount')
    parent_id = fields.Many2one('deputation.cities.allowance')

    @api.onchange('parent_id')
    def _onchange_existing_positions_ids(self):
        for record in self:
            domain = [('id', 'not in', self.parent_id.allowance_ids.job_position_ids.ids)]
            return {'domain': {'job_position_ids': domain}}
