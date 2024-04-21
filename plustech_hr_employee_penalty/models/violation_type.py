from odoo import fields, models


class ViolationViolation(models.Model):
    _name = 'violation.violation'
    _order = 'sequence, id'
    _description = 'Violations'

    name = fields.Char(string='Violation Type', translate=True)
    penalty_ids = fields.One2many('penalty.penalty', 'violation_id', string='Penalty')
    sequence = fields.Integer(default=1)


class PenaltyStage(models.Model):
    _name = 'penalty.stage'
    _check_company_auto = True
    _description = 'Penalty stage'

    name = fields.Char(string='Name', translate=True)
    salary_deduction = fields.Boolean(string='Salary Deduction?')
    salary_type = fields.Selection([('gross', 'Gross Salary'), ('basic', 'Basic Salary'),
                                    ('selected_allowance', 'Basic + Selected Allowances')])
    allowance_ids = fields.Many2many('employee.allowance.type', string='Allowances')
    deduction_type = fields.Selection([('fixed', 'Fixed Amount'), ('percentage', 'Percentage'),
                                       ('days', 'Days')],
                                      default='percentage', string='Percentage Type')
    warning = fields.Boolean(string='Warning?')
    contract_termination = fields.Boolean(string='Contract Termination With EOS?')
    without_eos = fields.Boolean(string='Termination Without EOS?')
    deduct_amount = fields.Float(string='Deduction Amount/Days',
                                 help='Fixed: deduct fixed amount from payslip gross\n'
                                      'Percentage: A percentage of the daily salary '
                                      'is deducted\n Days: The daily salary is deducted'
                                      ' according to the number of days')
    one_time = fields.Boolean(string='One-time deprivation of promotion or bonus')
    penalty_id = fields.Many2one('penalty.penalty', string='Penalty')
    company_id = fields.Many2one(
        string='Company',
        comodel_name='res.company',
        required=True,
        default=lambda self: self.env.company
    )


# class PenaltiesHistory(models.Model):
#     _name = 'penalty.history'
#     _description = 'Penalty History'
#
#     date = fields.Date(string='Date')
#     name = fields.Char('Penalty')
#     employee_id = fields.Many2one('hr.employee', string='Employee')
#     penalty_id = fields.Many2one('hr.punishment')


class PenaltyPenalty(models.Model):
    _name = 'penalty.penalty'
    _check_company_auto = True
    _description = 'Penalties'

    name = fields.Char(string='Name', translate=True)
    violation_id = fields.Many2one('violation.violation', string='Violation', required=True)
    stage_ids = fields.One2many('penalty.stage', 'penalty_id', string='Stages')
    company_id = fields.Many2one(
        string='Company',
        comodel_name='res.company',
        required=True,
        default=lambda self: self.env.company
    )
