# -*- coding: utf-8 -*-

from odoo import models, fields, _
from odoo.exceptions import ValidationError


class TrainingTraining(models.Model):
    _inherit = 'training.training'

    deserve_perdiem = fields.Boolean(string='Deserve Per-Diem')
    business_trip_ids = fields.One2many('hr.deputation', 'training_request_id', string='Per-Diem')

    def action_hr_approve(self):
        res = super(TrainingTraining, self).action_hr_approve()
        if self.deserve_perdiem and not self.business_trip_ids:
            raise ValidationError(_("This Training request deserve per-diem please create business trip"))
        return res

    def action_generate_trip(self):
        result = self.env.ref('plustech_hr_business_trip.action_hr_deputation').read()[0]
        view_id = self.env.ref('plustech_hr_business_trip.view_hr_deputation_form').id
        result.update({'views': [(view_id, 'form')], })
        # deputation_id = self.env['deputation.cities.allowance'].search([('to_city_id', '=', self.city_id.id)])
        deputation_id = self.env['deputation.cities.allowance'].search([]).filtered(lambda l: self.country_id.id in l.country_ids.ids)
        if not deputation_id:
            raise ValidationError(_("This Training request deserve per-diem please create business trip"))

        result['context'] = {
            'default_employee_id': self.employee_id.id,
            'default_deputation_type': 'external',
            'default_deputation_id': deputation_id.id,
            'default_from_date': self.start_date,
            'default_to_date': self.end_date,
            'default_training_request_id': self.id,
            'default_to_city_id': self.city_id.id,
            'default_destination_country_id': self.country_id.id,
            'default_description': self.name,
        }
        return result

    def action_trip_view(self):
        self.ensure_one()
        action, = self.env.ref('plustech_hr_business_trip.action_hr_deputation').read()
        action['context'] = {'create': False}
        action['domain'] = [('training_request_id', '=', self.id)]
        return action
