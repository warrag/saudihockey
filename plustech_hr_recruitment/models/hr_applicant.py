from odoo import fields, models, api


class HRApplicant(models.Model):
    _inherit = 'hr.applicant'

    birth_date = fields.Date(string='Birth Date')
    nationality_id = fields.Many2one('res.country', string='Nationality')
    religion = fields.Many2one('employee.religion', string='Religion')
    identification_id = fields.Char(string='ID/Iqama')
    id_issue_place = fields.Char(string='Place Of Issue')
    id_expire_date = fields.Date(string='Date Of Expire')
    passport_no = fields.Char(string='No. Of Passport')
    passport_issue_place = fields.Char(atring='Place Oof Issue')
    passport_expire = fields.Date(string='Date Of Expire')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Gender', default='male')
    marital = fields.Selection([('single', 'Single'), ('married', 'Married'),
                                ('widower', 'Widower'), ('divorced', 'Divorced'),
                                ], string='Marital Status', default='single')
    education_ids = fields.One2many('hr.resume.line', 'edu_job_id')
    training_course_ids = fields.One2many('hr.resume.line', 'course_job_id')
    skill_ids = fields.One2many('hr.employee.skill', 'applicant_id')
    dependent_ids = fields.One2many('hr.employee.family', 'application_id')


class HrResumeLine(models.Model):
    _inherit = 'hr.resume.line'

    edu_job_id = fields.Many2one('hr.applicant')
    course_job_id = fields.Many2one('hr.applicant')


class HrEmployeeSkill(models.Model):
    _inherit = 'hr.employee.skill'

    applicant_id = fields.Many2one('hr.applicant')


class EmployeeFamily(models.Model):
    _inherit = 'hr.employee.family'

    application_id = fields.Many2one('hr.applicant')


