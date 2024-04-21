# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    deputation_id = fields.Many2one('hr.deputation', string='Deputation Request')

    def action_post(self):
        result = super(AccountPayment, self).action_post()
        if self.deputation_id:
            business_trip_activity_obj = self.env['business.trip.activity'].search([('business_trip_state', '=', self.deputation_id.state)])
            self.sudo()._get_user_approval_activities(user=self.env.user, activity_type=business_trip_activity_obj.activity_type_id, record=self.deputation_id).action_feedback()
            self.deputation_id.write({'state':'paid'})
            self.create_activity(self.deputation_id, 'paid')

        return result

    def _get_user_approval_activities(self, user, activity_type, record):
        domain = [
            ('res_model', '=', 'hr.deputation'),
            ('res_id', 'in', record.ids),
            ('activity_type_id', '=', activity_type.id),
            ('user_id', '=', user.id)
        ]
        activities = self.env['mail.activity'].search(domain)
        return activities

    def create_activity(self, record, state, user=False,):
        business_trip_activity_obj = self.env['business.trip.activity'].search([('business_trip_state', '=', state)])
        if business_trip_activity_obj:
            self.env['mail.activity'].sudo().create({
                'activity_type_id': business_trip_activity_obj.activity_type_id.id,
                'res_id': record.id,
                'res_model_id': self.env['ir.model'].sudo().search([('model', '=', 'hr.deputation')], limit=1).id,
                'icon': 'fa-pencil-square-o',
                'date_deadline': fields.Date.today(),
                'user_id': business_trip_activity_obj.users_id.id,
                'summary': business_trip_activity_obj.subject if business_trip_activity_obj.subject else False,
                'note': business_trip_activity_obj.note,
            })

