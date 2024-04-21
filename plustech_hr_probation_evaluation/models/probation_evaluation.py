from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import datetime
from dateutil.relativedelta import relativedelta


class ProbationEvaluation(models.Model):
    _name = 'probation.evaluation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Probation Evaluation'
    _rec_name = 'employee_id'

    @api.model
    def default_get(self, default_fields):
        vals = super(ProbationEvaluation, self).default_get(default_fields)
        lines = []
        for item in self.env['probation.evaluation.item'].search([]):
            line = (0, 0, {
                'item_id': item.id,
            })
            lines.append(line)
        vals['line_ids'] = lines
        return vals

    employee_id = fields.Many2one('hr.employee', string='Employee')
    employee_no = fields.Char(related='employee_id.employee_number', string='Employment No')
    job_id = fields.Many2one(related='employee_id.job_id', string='Job Title')
    join_date = fields.Date(related='employee_id.join_date', string='Joint Date')
    manager_id = fields.Many2one(related='employee_id.parent_id', string='Manager')
    department_id = fields.Many2one('hr.department', related='employee_id.department_id', string='Department')
    evaluation_date = fields.Date(string='Evaluation Date',
                                  help='Date of the evaluation, automatically updated when the evaluation is Done or '
                                       'Cancelled.', required=True, index=True,
                                  default=lambda self: datetime.date.today())
    total_points = fields.Integer(string='Total Points', compute='compute_points')
    average = fields.Float(string='Average Evaluation')
    manager_recommendation = fields.Text(string='Recommendations', help='employee direct manager recommendations')
    manager_recommendation_date = fields.Date(string='Date', help='employee direct manager recommendation date')
    department_manager_id = fields.Many2one(related='department_id.manager_id', string='Department Manager')
    dempt_manager_recommendation = fields.Text(string='Recommendations', help='department manager recommendations')
    dept_manager_recommendation_date = fields.Date(string='Date', help='department manager recommendation date')
    hr_responsible = fields.Many2one('res.users', string='HR Responsible',
                                     help='human resources department responsible')
    hr_recommendation = fields.Text(string='Recommendation', help='Hr department recommendations')
    hr_recommendation_date = fields.Date(string='Date', help='Hr department recommendation date')
    evaluation_result = fields.Selection([('retain', 'Employee Retention'),
                                          ('termination', 'Termination'),
                                          ('extend', 'Probation period extension')])
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed'),
                              ('done', 'Done'), ('cancel', 'Cancelled')], string='Status', default='draft')
    image_128 = fields.Image(related='employee_id.image_128')
    image_1920 = fields.Image(related='employee_id.image_1920')
    avatar_128 = fields.Image(related='employee_id.avatar_128')
    avatar_1920 = fields.Image(related='employee_id.avatar_1920')
    previous_evaluation_id = fields.Many2one('probation.evaluation', related='contract_id.previous_evaluation_id',
                                             string='Previous Evaluation')
    previous_evaluation_date = fields.Date(related='previous_evaluation_id.evaluation_date')
    company_id = fields.Many2one('res.company', related='employee_id.company_id', store=True)
    contract_id = fields.Many2one('hr.contract', related='employee_id.contract_id')
    trial_end_date = fields.Date(related='contract_id.trial_date_end', string='Trial End Date')
    line_ids = fields.One2many('probation.evaluation.line', 'evaluation_id')

    def action_open_last_evaluation(self):
        self.ensure_one()
        return {
            'view_mode': 'form',
            'res_model': 'probation.evaluation',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': self.previous_evaluation_id.id,
        }

    @api.depends('line_ids.rate')
    def compute_points(self):
        points = 0.0
        for record in self:
            for line in record.line_ids:
                points += int(line.rate)
            record.total_points = points
            record.average = (record.total_points/(len(record.line_ids)*4))*100 if record.total_points > 0 else 0.0
            points = 0.0

    def action_confirm(self):
        self.state = 'confirmed'

    def action_done(self):
        if not self.evaluation_result:
            raise ValidationError(_('Please set evaluation result'))
        for contract in self.employee_id.contract_id:
            if self.evaluation_result == 'extend':
                duration = contract.trial_date_end - contract.date_start
                line_dict = {
                    'start_date': contract.trial_date_end,
                    'end_date': contract.trial_date_end + relativedelta(days=+duration.days),
                    'duration': duration.days,
                    'job_id': contract.job_id.id
                }
                new_line = self.env['employee.trial.period.history'].new(line_dict)
                contract.period_history_ids += new_line
            elif self.evaluation_result == 'termination':
                contract.state = 'cancel'
            contract.previous_evaluation_id = self.id
        self.state = 'done'

    def action_cancel(self):
        self.state = 'cancel'


class ProbationEvaluationLines(models.Model):
    _name = 'probation.evaluation.line'
    _description = 'Probation Evaluation Line'

    no = fields.Char(string='No#', compute="_compute_number")
    item_id = fields.Many2one('probation.evaluation.item', string='Evaluation Item')
    degree = fields.Selection([('0', 'Very weak'), ('1', 'weak'), ('2', 'Good'),
                               ('3', 'Very Good'), ('4', 'Excellent'),
                               ], default='0', string='Degree', compute='compute_degree')
    rate = fields.Selection([
        ('0', 'Very weak'), ('1', 'weak'), ('2', 'Good'),
        ('3', 'Very Good'), ('4', 'Excellent'),
    ], default='0', index=True, string="Rating", tracking=True)
    evaluator_id = fields.Many2one('res.users', 'Evaluated By')
    evaluation_id = fields.Many2one('probation.evaluation')

    @api.depends('evaluation_id')
    def _compute_number(self):
        no = 1
        for line in self.evaluation_id.line_ids:
            line.no = no
            no += 1

    @api.depends('rate')
    def compute_degree(self):
        for line in self:
            line.degree = line.rate
            if not line.evaluator_id:
                line.evaluator_id = self.env.user


class ProbationEvaluationItem(models.Model):
    _name = 'probation.evaluation.item'
    _description = 'Probation Evaluation Item'

    name = fields.Char(string='Name', translate=True)
    active = fields.Boolean(string='Active', default=True)
