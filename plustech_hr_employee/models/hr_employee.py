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

from datetime import date
from dateutil import relativedelta
from odoo import models, fields, _
from odoo import api
from odoo.exceptions import ValidationError, UserError, Warning
from odoo.osv import expression


def is_leap_year(year):
    return (year % 4 == 0) and (year % 100 != 0) or (year % 400 == 0)


GENDER_SELECTION = [('male', 'Male'),
                    ('female', 'Female'),
                    ('other', 'Other')]


class HrEmployeeContractName(models.Model):
    """This class is to add emergency contact table"""
    _name = 'hr.emergency.contact'
    _description = 'HR Emergency Contact'

    name = fields.Char(string='Name')
    number = fields.Char(string='Number', help='Contact Number')
    employee_id = fields.Many2one('hr.employee', invisible=1)
    relation = fields.Selection([('father', 'Father'), ('mother', 'Mother'),
                                 ('daughter', 'Daughter'), ('son', 'Son'),
                                 ('spouse', 'Spouse'), ('friend', 'Friend'), ('other', 'Other')],
                                string='Relationship', help='Relation with employee')


class HrEmployeeFamilyInfo(models.Model):
    """Table for keep employee family information"""
    _name = 'hr.employee.family'
    _description = 'HR Employee Family'
    _rec_name = 'member_name'

    member_name = fields.Char(string='Name')
    employee_id = fields.Many2one(string="Employee", help='Select corresponding Employee', comodel_name='hr.employee',
                                  invisible=1)
    relation = fields.Selection([('father', 'Father'),
                                 ('mother', 'Mother'),
                                 ('daughter', 'Daughter'),
                                 ('son', 'Son'),
                                 ('spouse', 'Spouse')], string='Relationship', help='Relation with employee')
    birth_date = fields.Date(string='Date Of Birth')
    age = fields.Integer(compute="compute_age")
    identification_no = fields.Char(string='ID Number')

    @api.depends('birth_date')
    def compute_age(self):
        delta = 0
        for rec in self:
            if rec.birth_date:
                delta = relativedelta.relativedelta(date.today(), rec.birth_date).years
            rec.age = delta


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    name = fields.Char(translate = True)
    # english_name = fields.Char(string="Name In English")
    personal_mobile = fields.Char(string='Mobile', store=True)
    emergency_contact_ids = fields.One2many('hr.emergency.contact', 'employee_id', string='Emergency Contact')
    join_date = fields.Date(string='Joining Date')
    id_expiry_date = fields.Date(string='Expiry Date', help='Expiry date of Identification ID')
    passport_expiry_date = fields.Date(string='Expiry Date', help='Expiry date of Passport ID')
    passport_issue_location = fields.Char(string="Place of Issue")
    passport_issue_date = fields.Date(string='Date of Issue', help='issuing date of Passport ID')
    fam_ids = fields.One2many('hr.employee.family', 'employee_id', string='Family', help='Family Information')
    employee_id = fields.Char(store=True, readonly=True)
    employee_qr_code = fields.Binary("QR Code")
    employee_number = fields.Char(string='Employee Number')
    religion_id = fields.Many2one('employee.religion')
    membership_number = fields.Char(string='Membership Number')
    membership_expire_date = fields.Date(string='Membership Expire Date')
    membership_name = fields.Char(string='Membership Name')
    membership_type = fields.Char(string='Membership Type')
    user_type = fields.Selection([('internal', 'Internal'), ('portal', 'Portal')],
                                 string='User Type', default='internal')
    certificate = fields.Selection(selection_add=[('elementary', 'Elementary'), ('intermediate', 'Intermediate'),
                                                  ('graduate',), ('diploma', 'Diploma'), ('bachelor',)],
                                   ondelete={'elementary': 'set default', 'diploma': 'set default'})
    id_generation_method = fields.Selection([('manual', 'Manual Entry'), ('auto', 'Auto Generation')],
                                            string='Employee ID Generation Method', default='manual')
    employee_sequence_id = fields.Many2one('ir.sequence', string='ID Sequence')
    social_insurance = fields.Char('Social insurance')
    id_attachment_id = fields.Many2many('ir.attachment', 'id_attachment_rel', 'id_ref', 'attach_ref',
                                        string="Attachment", help='You can attach the copy of your Id')
    passport_attachment_id = fields.Many2many('ir.attachment', 'passport_attachment_rel', 'passport_ref', 'attach_ref1',
                                              string="Attachment",
                                              help='You can attach the copy of Passport')

    _sql_constraints = [
        ('emp_user_id_uniq', 'unique(user_id)', "A user cannot be linked to multiple employees.")
    ]

    @api.onchange('job_id')
    def onchange_job_id(self):
        if self.job_id:
            self.department_id = self.job_id.department_id

    @api.onchange('user_type')
    def onchange_user_type(self):
        domain = []
        if self.user_type == 'internal':
            domain = [('share', '=', False)]
        elif self.user_type == 'portal':
            domain = [('share', '=', True)]
        return {'domain': {'user_id': domain}}

    def create_portal_user(self):
        for record in self:
            vals = {
                'company_id': self.env.ref('base.main_company').id,
                'name': self.name,
                'login': self.address_home_id.email or self.work_email,
                'email': self.work_email,
                'partner_id': self.address_home_id.id,
                'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],
                'company_ids': [(6, 0, [self.company_id.id])],
                'company_id': self.company_id.id
            }
            user = self.env['res.users'].sudo().create(vals)
            if user:
                record.user_id = user.id

    @api.constrains('employee_number')
    def _check_unique_employee_number(self):
        for rec in self:
            employees = self.env['hr.employee'].search(
                [('id', '!=', rec.id), ('employee_number', '=', rec.employee_number),
                 ('company_id', '=', rec.company_id.id)])
            if employees:
                raise ValidationError(_('Employee Number must be unique!'))

    @api.onchange('user_id')
    def _onchange_related_user_id(self):
        self.address_home_id = self.user_id.partner_id.id

    def get_days_diff(self, end_date):
        days_to_expire = 0
        today = fields.Datetime.now().date()
        if today <= end_date:
            delta = end_date - today
            days_to_expire = delta.days
        return days_to_expire

    def set_partner(self):
        employees = self.env['hr.employee'].search([('id', 'in', self.env.context.get('active_ids', [])),
                                                    ('address_home_id', '=', False)])
        for emp in employees:
            if emp.user_id:
                emp.address_home_id = emp.user_id.partner_id.id
            else:
                address_home_id = self.env['res.partner'].create({
                    'name': emp.name,
                    'company_type': 'person',
                    'employee': True
                })
                if address_home_id:
                    emp.address_home_id = address_home_id.id

    def expiration_date_reminder(self):
        match = self.search([])
        for record in match:

            if record.id_expiry_date:
                id_expire_days = self.get_days_diff(record.id_expiry_date)
                if id_expire_days <= record.company_id.id_days:
                    mail_content = "  Hello  " + record.name + ",<br>Employee ID " + record.identification_id + " is going to expire on " + \
                                   str(record.id_expiry_date) + ". Please renew it before expiry date"
                    subject = _('ID - %s Expired On %s') % (record.identification_id, record.id_expiry_date)

                    try:
                        if record.company_id.id_reminder_user_ids:
                            # self._send_mail(subject, mail_content, record.work_email).send()
                            self._send_notification(record.id, subject, mail_content, record.company_id.id_reminder_user_ids)
                    except:
                        pass

            if record.membership_number and record.membership_expire_date:
                membership_expire_days = self.get_days_diff(record.membership_expire_date)
                if membership_expire_days <= self.env.user.company_id.membership_days:
                    mail_content = "  Hello  " + record.name + ",<br>Employee Membership " + record.membership_number + " is going to expire on " + \
                                   str(record.membership_expire_date) + ". Please renew it before expiry date"

                    subject = _('Membership-%s Expired On %s') % (record.membership_number, record.membership_expire_date),

                    try:
                        if record.company_id.membership_reminder_user_ids:
                            self._send_notification(record.id, mail_content, subject,
                                                    record.company_id.membership_reminder_user_ids)

                    except:
                        pass

            if record.passport_expiry_date:
                passport_expire_days = self.get_days_diff(record.passport_expiry_date)
                if passport_expire_days <= self.env.user.company_id.passport_days:
                    mail_content = "  Hello  " + record.name + ",<br>Employee Passport " + record.passport_id + " is going to expire on " + \
                                   str(record.passport_expiry_date) + ". Please renew it before expiry date"

                    subject = _('Passport-%s Expired On %s') % (record.passport_id, record.passport_expiry_date),

                    try:
                        if record.company_id.passport_reminder_user_ids:
                            self._send_notification(record.id, subject, mail_content,
                                                    record.company_id.passport_reminder_user_ids)
                    except:
                        pass

    # def _send_mail(self, subject, body, sender):
    #     main_content = {
    #         'subject': subject,
    #         'author_id': self.env.user.partner_id.id,
    #         'body_html': body,
    #         'email_to': sender,
    #     }
    #     mail_id = self.env['mail.mail'].create(main_content)
    #     return mail_id

    def _send_notification(self, res_id, summary, note, users):
        for user in users:
            notification = {
                'activity_type_id': self.env.ref(
                    'plustech_hr_employee.document_expire_notification').id,
                'res_id': res_id,
                'res_model_id': self.env['ir.model'].search([('model', '=', 'hr.employee')], limit=1).id,
                'icon': 'fa-pencil-square-o',
                'date_deadline': fields.Date.today(),
                'user_id': user.id,
                'note': note,
                'summary': summary,
            }
            try:
                self.env['mail.activity'].create(notification)
            except:
                pass

    @api.model
    def _get_join_date(self):
        contract_id = self.env['hr.contract'].search([('employee_id', '=', self.id), '|',
                                                      ('state', '=', 'close'),
                                                      ('state', '=', 'open')
                                                      ], order='id asc', limit=1)
        if contract_id:
            self.join_date = contract_id.date_start

    @api.model
    def create(self, vals):
        if self.identification_id:
            if len(vals['identification_id']) < 10 or len(vals['identification_id']) > 10:
                # raise UserError(_('Exists the discount limit'))
                raise ValidationError(_('The identification No. should be 10 digits'))

        sequ_id = self.env['ir.sequence'].next_by_code('hr.employee')
        vals['employee_id'] = sequ_id

        res = super(HrEmployee, self).create(vals)
        # vals['barcode'] = sequ_id
        for record in res:
            if record.id_attachment_id:
                record.id_attachment_id.write({'res_model': self._name, 'res_id': record.id})
            if record.passport_attachment_id:
                record.passport_attachment_id.write({'res_model': self._name, 'res_id': record.id})
        return res

    def write(self, values):
        for record in self:
            if not record.employee_id:
                sequ_id = self.env['ir.sequence'].next_by_code('hr.employee')
                values['employee_id'] = sequ_id
            if record.id_attachment_id:
                record.id_attachment_id.write({'res_model': self._name, 'res_id': record.id})
            if record.passport_attachment_id:
                record.passport_attachment_id.write({'res_model': self._name, 'res_id': record.id})
        return super(HrEmployee, self).write(values)

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('employee_number', '=ilike', name.split(' ')[0] + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    # english_name = fields.Char(string="Name In English")
    personal_mobile = fields.Char(string='Mobile', store=True)
    join_date = fields.Date(string='Joining Date')
    id_expiry_date = fields.Date(string='Expiry Date', help='Expiry date of Identification ID')
    passport_expiry_date = fields.Date(string='Expiry Date', help='Expiry date of Passport ID')
    passport_issue_location = fields.Char(string="Place of Issue")
    passport_issue_date = fields.Date(string='Date of Issue', help='issuing date of Passport ID')
    employee_number = fields.Char(string='Employee Number', required=True)
    religion_id = fields.Many2one('employee.religion')
    membership_number = fields.Char(string='Membership Number')
    membership_expire_date = fields.Date(string='Membership Expire Date')
    membership_name = fields.Char(string='Membership Name')
    membership_type = fields.Char(string='Membership Type')
    name = fields.Char(compute='_calc_name', store=True, translate=True, compute_sudo=True)
    user_type = fields.Selection([('internal', 'Internal'), ('portal', 'Portal')],
                                 string='User Type', default='internal')
    id_generation_method = fields.Selection([('manual', 'Manual Entry'), ('auto', 'Auto Generation')],
                                            string='Employee ID Generation Method', default='manual')
    employee_sequence_id = fields.Many2one('ir.sequence', string='ID Sequence')
    social_insurance = fields.Char('Social insurance')

    @api.depends('resource_id.name')
    @api.depends_context('lang')
    def _calc_name(self):
        for record in self:
            record.name = record.resource_id.name

    @api.model
    def _recompute_name(self):
        records = self.search([])
        self.env.add_to_compute(self._fields['name'], records)
        self.flush()