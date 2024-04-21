from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class JobRequest(models.Model):
    _name = 'job.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name')
    job_position_id = fields.Many2one('hr.job', copy=False)
    request_date = fields.Date(string='Date', required=True, default=fields.Date.today())
    create_job_position_id = fields.Many2one('hr.job', copy=False)
    department_id = fields.Many2one('hr.department', required=1, copy=False)
    user_id = fields.Many2one('res.users', required=1, copy=False, default=lambda self: self.env.user)
    reason = fields.Text('Reason', copy=False)
    job_goal = fields.Text('Goals', copy=False)
    tasks = fields.Text('Responsibilities and tasks', copy=False)
    qualifications = fields.Text('Qualifications', copy=False)
    competencies = fields.Char('Competencies', copy=False)
    academic = fields.Char('Academic Qualification', copy=False)
    degree = fields.Char('degree', copy=False)
    year_exp = fields.Char('Years Of Experience', copy=False)
    salary = fields.Float('salary', copy=False)
    notes = fields.Text('notes', copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('depart_approve', 'Department Approve'),
        ('hr_approve', 'Hr Approve'),
        ('ceo_approve', 'Ceo Approve'),
    ], string='Status', readonly=True, required=True, tracking=True, copy=False, default='draft',
        help="Set whether the recruitment process is open or closed for this job position.")
    is_depart_manger = fields.Boolean(compute="get_is_depart_manger")
    is_hr_user = fields.Boolean(compute="get_is_hr_user")
    no_of_recruitment = fields.Integer('Expected New Employees')

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('job.request') or _('New')
        return super(JobRequest, self).create(vals)

    @api.depends('department_id')
    def get_is_hr_user(self):
        for rec in self:
            rec.is_hr_user = False
            if rec.env.user.has_group('hr.group_hr_user'):
                rec.is_hr_user = True

    @api.depends('department_id')
    def get_is_depart_manger(self):
        for rec in self:
            rec.is_depart_manger = False
            if rec.department_id:
                if rec.department_id.manager_id:
                    if rec.department_id.manager_id.user_id == self.env.user:
                        rec.is_depart_manger = True

    def set_depart_approve(self):
        if self.no_of_recruitment <= 0:
            raise ValidationError(_("No of Expected New Employees Must Bigger Than Zero"))
        self.write({'state': 'depart_approve'})
        return True

    def set_hr_approve(self):
        self.write({'state': 'hr_approve'})
        return True

    def set_ceo_approve(self):
        self.write({'state': 'ceo_approve'})
        if not self.job_position_id:
            job_id = self.env['hr.job'].create({
                'name': self.name,
                'department_id': self.department_id.id,
                'no_of_recruitment': self.no_of_recruitment,
            })
            self.create_job_position_id = job_id.id
        return True

    def action_confirm(self):
        self.write({'state': 'confirm'})
        return True
