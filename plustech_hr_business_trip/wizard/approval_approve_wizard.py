# -*- coding: utf-8 -*-

from odoo import models, fields, _
from datetime import date

STATUS = {'new': 'Create',
          'direct_manager': 'Direct Manager Approval',
          'acceptance': 'Employee Acceptance',
          'hr': 'Human Resources Approval',
          'hrm': 'HRM Approval',
          'finance': 'Director of Financial and Administrative Affairs Approval',
          'ceo': 'CEO Approval',
          'to_pay': 'To Pay',
          'paid': 'Register Payment'
        }


class ApprovalRejectWizard(models.TransientModel):
    _name = 'approval.approve.wizard'
    _description = 'Approval Approve Wizard'

    reason = fields.Text()

    def action_approve(self):
        model = self._context.get('active_model')
        record_id = self._context.get('active_id')
        record = self.env[model].browse(record_id)
        if self.env.context.get('triggered_action'):
            action = self.env.context.get('triggered_action')
            record.write({
                'approval_ids': [(0, 0, {'user_id': self.env.user.id, 
                                         'name': STATUS[record.state],
                                         'comment': self.reason, 
                                         'state': 'approved', 
                                         'key': record.state, 
                                         'date': date.today()})],
            })
            eval("self." + action + "(record)")

    def action_employee_acceptance(self, trip):
        for record in trip:
            business_trip_activity_obj = self.env['business.trip.activity'].sudo().search([('type','=','trip'),('business_trip_state', '=', record.state)])
            if business_trip_activity_obj:
                for obj in business_trip_activity_obj:
                    self._action_feedback_activity(self.env.user,obj.activity_type_id,trip)
            record.write({'state': 'hr'})
            self.create_activity(trip, 'hr')

    def action_direct_manager_approve(self, trip):
        for record in trip:
            business_trip_activity_obj = self.env['business.trip.activity'].search([('type','=','trip'),('business_trip_state', '=', record.state)])
            if business_trip_activity_obj:
                for obj in business_trip_activity_obj:
                    self._action_feedback_activity(self.env.user,obj.activity_type_id,trip)
            record.write({'state': 'hr'})
            self.create_activity(trip, 'hr')

    def action_hr_officer_approve(self, trip):
        for record in trip:
            business_trip_activity_obj = self.env['business.trip.activity'].search([('type','=','trip'),('business_trip_state', '=', record.state)])
            if business_trip_activity_obj:
                for obj in business_trip_activity_obj:
                    self._action_feedback_activity(self.env.user,obj.activity_type_id,trip)
            record.write({'state': 'hrm'})
            self.create_activity(trip, 'hrm')

    def action_hr_manager_approve(self, trip):
        for record in trip:
            business_trip_activity_obj = self.env['business.trip.activity'].search([('type','=','trip'),('business_trip_state', '=', record.state)])
            if business_trip_activity_obj:
                for obj in business_trip_activity_obj:
                    self._action_feedback_activity(self.env.user,obj.activity_type_id,trip)
            record.write({'state': 'finance'})
            self.create_activity(trip, 'finance')

    def action_finance_approve(self, trip):
        for record in trip:
            business_trip_activity_obj = self.env['business.trip.activity'].search([('type','=','trip'),('business_trip_state', '=', record.state)])
            if business_trip_activity_obj:
                for obj in business_trip_activity_obj:
                    self._action_feedback_activity(self.env.user,obj.activity_type_id,trip)
            record.write({'state': 'ceo'})
            self.create_activity(trip, 'ceo')

    def action_ceo_approve(self, trip):
        for record in trip:
            business_trip_activity_obj = self.env['business.trip.activity'].search([('type','=','trip'),('business_trip_state', '=', record.state)])
            if business_trip_activity_obj:
                for obj in business_trip_activity_obj:
                    self._action_feedback_activity(self.env.user,obj.activity_type_id,trip)
            record.write({'state': 'to_pay'})
            self.create_activity(trip, 'to_pay')

    def get_users(self, group_id):
        users_ids = self.env['res.users'].search(
            [('groups_id', '=', group_id), ('login', 'not in', ['admin', str(self.env.user.company_id.email)])])
        return users_ids

    def create_activity(self, record, state, user=False,):
        business_trip_activity_obj = self.env['business.trip.activity'].sudo().search([('business_trip_state', '=', state)])
        if business_trip_activity_obj:
            for obj in business_trip_activity_obj:
                self.env['mail.activity'].sudo().create({
                    'activity_type_id': obj.activity_type_id.id,
                    'res_id': record.id,
                    'res_model_id': self.env['ir.model'].sudo().search([('model', '=', 'hr.deputation')], limit=1).id,
                    'icon': 'fa-pencil-square-o',
                    'date_deadline': fields.Date.today(),
                    'user_id': obj.users_id.id,
                    'summary': obj.subject if obj.subject else False,
                    'note': obj.note,
                })

    def _log_message(self, user_ids, record):
        for rec in record:
            notifications_ids = []
            for responsible in user_ids:
                notifications_ids.append([0, 0, {
                    "res_partner_id": responsible.partner_id.id,
                    "notification_type": "inbox"
                }])
            self.env["mail.message"].create({
                "message_type": "notification",
                "body": _("Business Trip") + " %s " % rec.name + _("approval."),
                "subject": _("Business Trip") + " %s " % rec.name + _("is need your approval."),
                "model": 'hr.deputation',
                "res_id": rec.id,
                "partner_ids": [(6, 0, user_ids.partner_id.ids)],
                "author_id": self.env.user.partner_id.id,
                "notification_ids": notifications_ids
            })

    def _action_feedback_activity(self, user, activity_type, record):
            self.sudo()._get_user_approval_activities(user=user, 
                                                      activity_type=activity_type,
                                                      record=record).action_feedback()

    def _get_user_approval_activities(self, user, activity_type, record):
        domain = [
            ('res_model', '=', 'hr.deputation'),
            ('res_id', 'in', record.ids),
            ('activity_type_id', '=', activity_type.id),
        ]
        activities = self.env['mail.activity'].search(domain)
        return activities
