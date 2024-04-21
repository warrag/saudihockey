from odoo import fields, models, api, _
from odoo.exceptions import UserError


class HrAppraisalTemplate(models.Model):
    _name = 'hr.appraisal.template'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'HR Appraisal Template'

    name = fields.Char(string='Name', translate=True, required=True, tracking=True)
    description = fields.Html(string='Description', translate=True)
    objectives_percentage = fields.Float(string='Objectives Percentage', default=60, tracking=True)
    competencies_percentage = fields.Float(string='Competencies Percentage', default=40, tracking=True)
    min_objectives = fields.Integer(string='Min Objectives', help="Minimum number of annual objectives",
                                    default=3)
    min_competencies = fields.Integer(string='Min Competencies', help="Minimum number of competencies",
                                      default=3)
    max_objectives = fields.Integer(string='Max Objectives', help="Maximum number of annual objectives",
                                    default=5)
    max_competencies = fields.Integer(string='Max Competencies', help="Maximum number of competencies",
                                      default=4)
    deadline_reminder = fields.Integer(string='Deadline Reminder Days', default=15)
    evaluation_escale_ids = fields.One2many('hr.appraisal.evaluation.scale', 'template_id')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    appraisal_weight_ids = fields.Many2many('appraisal.weight', string='Weights',
                                            tracking=True, required=True)
    type = fields.Selection(
        string='Type',
        selection=[('supervisory', 'Supervisory'),
                   ('non_supervisory', 'Non Supervisory'), ],
        required=False, )



class EvaluationScale(models.Model):
    _name = "hr.appraisal.evaluation.scale"
    _description = "Appraisal Evaluation Scale"

    name = fields.Char(string='Name', translate=True, required=True)
    rate_from = fields.Float(string='Rate From', required=True)
    rate_to = fields.Float(string='Rate To', required=True)
    template_id = fields.Many2one('hr.appraisal.template', ondelete="cascade")

    @api.constrains('rate_from', 'rate_to')
    def _check_rate(self):
        for record in self:
            if record.rate_from >= record.rate_to:
                raise UserError(_("Rate from must be less than rate to"))


class AppraisalWeight(models.Model):
    _name = 'appraisal.weight'
    _description = 'Appraisal Weight'
    _rec_name = 'weight'

    weight = fields.Float(string='Weight')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)



