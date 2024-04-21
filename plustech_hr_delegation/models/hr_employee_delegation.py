from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class HrEmployeeDelegation(models.Model):
    _name = 'hr.employee.delegation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Employee Delegation'

    name = fields.Char()
    employee_id = fields.Many2one('hr.employee', string='Employee', default=lambda self: self.env.user.employee_id,
                                  required=True)
    department_id = fields.Many2one('hr.department', string='Department Name', related='employee_id.department_id')
    job_id = fields.Many2one('hr.job', string='Job Title', related='employee_id.job_id')
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.user.company_id.id)
    request_date = fields.Date(string='Request Date', default=fields.Date.today())
    attachment_number = fields.Integer('Number of Attachments', compute='get_attachment_ids')
    description = fields.Text(string='Description')
    from_date = fields.Date(string='From Date', required=True)
    to_date = fields.Date(string='To date', required=True)
    delegated_employee_id = fields.Many2one('hr.employee', string='Delegated Employee', required=True)
    state = fields.Selection([
        ('draft', 'To Submit'),
        ('submit', 'To Confirm'),
        ('cancel', 'Cancelled'),
        ('confirm', 'To Approve'),
        ('refuse', 'Refused'),
        ('validate', 'Approved')
    ], string='Status', readonly=True, tracking=True, copy=False, default='draft',
    )

    def action_submit(self):
        self.write({'state': 'submit'})

    def action_manager_approve(self):
        self.write({'state': 'confirm'})

    def action_hr_approve(self):
        self.write({'state': 'validate'})

    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        res['domain'] = [('res_model', '=', 'hr.employee.delegation'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'hr.employee.delegation', 'default_res_id': self.id}
        return res

    def get_attachment_ids(self):
        for rec in self:
            rec.attachment_number = self.env['ir.attachment'].search_count(
                [('res_model', '=', 'hr.employee.delegation'),
                 ('res_id', '=', rec.id)])

    def attach_document(self, **kwargs):
        pass

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            seq_date = None
            if 'request_date' in vals:
                seq_date = fields.Datetime.context_timestamp(
                    self, fields.Datetime.to_datetime(vals['request_date']))
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'employee.delegation', sequence_date=seq_date) or _('New')
        result = super(HrEmployeeDelegation, self).create(vals)
        return result

    def unlink(self):
        for record in self:
            if record.state == 'draft':
                raise ValidationError(_("You can't delete record not in draft state"))
        res = super(HrEmployeeDelegation, self).unlink()
        return res
