from odoo import fields, models, api, _
from datetime import date


class MedicalInsuranceRecord(models.Model):
    _name = 'medical.insurance.record'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Medical Insurance Records'

    name = fields.Char(string='Insurance Company', required=True)
    policy_number = fields.Char(string='Policy Number', required=True)
    annual_premium = fields.Float(string='Annual Premium')
    description = fields.Text(string='Description')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    member_ids = fields.One2many('employee.insurance.record', 'parent_id')
    member_count = fields.Integer(string='Members', compute='members_count')
    color = fields.Integer('Color Index', default=5)

    def members_count(self):
        for record in self:
            record.member_count = len(record.member_ids)

    def action_view_members(self):
        return {
            'name': _('Members'),
            'view_mode': 'tree',
            'res_model': 'employee.insurance.record',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('plustech_hr_medical_insurance.employee_insurance_record_view_tree').id,
            'domain': [('parent_id', '=', self.id)],
            'context': {'search_default_group_employee_id': 1}
        }


class EmployeeInsuranceRecord(models.Model):
    _name = 'employee.insurance.record'

    employee_id = fields.Many2one('hr.employee', string='Employee Name')
    employee_number = fields.Char(string='Employee Number')
    name = fields.Char(string='name')
    amount = fields.Float(string='Amount')
    relation = fields.Selection([('father', 'Father'),
                                 ('mother', 'Mother'),
                                 ('daughter', 'Daughter'),
                                 ('son', 'Son'),
                                 ('spouse', 'Spouse')], string='Relationship', help='Relation with employee')
    age = fields.Integer(string='Age')
    parent_id = fields.Many2one('medical.insurance.record')
    insurance_class = fields.Char(string='Insurance Class')
    member_type = fields.Selection([('employee', 'employee'), ('dependent', 'Dependent')])


