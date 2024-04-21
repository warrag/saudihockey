from odoo import fields, models, api


class HrLetterFields(models.Model):
    _name = 'hr.letter.fields'
    _description = 'Letters Dynamic Fields'

    name = fields.Char(required=True,translate=True)
    technical_name = fields.Char()
    default_value = fields.Char(string='Default Value',translate=True)
    fill_by = fields.Selection(selection=[
        ('employee', 'Employee'),
        ('direct_mg', 'Direct Manager'),
        ('depart_mg', 'Department Manager'),
        ('hr_officer', 'HR Officer'),
        ('hr_Manager', 'HR Manager'),
        ('financial', 'Financial'),
        ('ceo', 'CEO'),
    ], string='Filling By')
    template_id = fields.Many2one('letter.letter')
    required = fields.Boolean(string='Required')
    visible = fields.Boolean(string='Visible')




