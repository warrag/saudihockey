# -*- coding: utf-8 -*-
###################################################################################
#    A part of plustech hr Project <www.plustech-it.com>
#
#   Plus Technology.
#    Copyright (C) 2022-TODAY PlusTech Technologies (<www.plustech-it.com>).
#    Author: Hassan Abdallah  (<hassanyahya101@gmail.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################

from odoo import api, fields, models, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    id_days = fields.Integer(string='Identification Days', required=True, default=30)
    passport_days = fields.Integer(string='Passport Days', required=True, default=180)
    membership_days = fields.Integer(string='Membership Days', default=30)
    id_generation_method = fields.Selection([('manual', 'Manual Entry'), ('auto', 'Auto Generation')],
                                            string='Employee ID Generation Method', default='manual')
    employee_sequence_id = fields.Many2one('ir.sequence', string='ID Sequence')
    id_reminder_user_ids = fields.Many2many('res.users',  'id_reminder_users_rel', 'x_id', 'user_id', string='Users')
    passport_reminder_user_ids = fields.Many2many('res.users', 'passport_reminder_users_rel', 'x_id', 'user_id',
                                                  string='Users')
    membership_reminder_user_ids = fields.Many2many('res.users', 'membership_reminder_users_rel', 'x_id', 'user_id',
                                                    string='Users')


class HRConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # company_id = fields.Many2one('res.company', string='Company', required=True,
    #                              default=lambda self: self.env.user.company_id)
    id_days = fields.Integer(string='Identification Days', required=True,
                             default=lambda self: self.env.user.company_id.id_days)
    passport_days = fields.Integer(string='Passport Days', required=True,
                                   default=lambda self: self.env.user.company_id.passport_days)
    membership_days = fields.Integer(string='Membership Days', required=True,
                                     default=lambda self: self.env.user.company_id.membership_days)
    default_id_generation_method = fields.Selection([('manual', 'Manual Entry'), ('auto', 'Auto Generation')],
                                                    string='Employee ID Generation Method', default_model="hr.employee",
                                                    related='company_id.id_generation_method', readonly=False)
    default_employee_sequence_id = fields.Many2one('ir.sequence', string='ID Sequence', default_model="hr.employee",
                                                   related='company_id.employee_sequence_id', readonly=False)
    id_reminder_user_ids = fields.Many2many('res.users',  'id_reminder_users_rel', 'x_id', 'user_id',
                                            string='Users', related="company_id.id_reminder_user_ids",
                                            readonly=False)
    passport_reminder_user_ids = fields.Many2many('res.users', 'passport_reminder_users_rel', 'x_id', 'user_id',
                                                  string='Users', readonly=False,
                                                  related="company_id.passport_reminder_user_ids")
    membership_reminder_user_ids = fields.Many2many('res.users', 'membership_reminder_users_rel', 'x_id', 'user_id',
                                                    string='Users', readonly=False,
                                                    related="company_id.membership_reminder_user_ids")
