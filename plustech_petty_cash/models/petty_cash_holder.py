from odoo import fields, models, api,_
from odoo.exceptions import ValidationError


class PettyUser(models.Model):
    _name = 'petty.user'
    _inherit = ['mail.thread']

    def _get_petty_account_id(self):
        return self.env.user.company_id.petty_account_id.id

    def _get_purchase_journal_id(self):
        return self.env.user.company_id.purchase_journal_id.id

    def _get_analytic_account_id(self):
        return self.env.user.company_id.petty_analytic_account_id.id

    def _get_limit(self):
        return self.env.user.company_id.limit

    company_id = fields.Many2one(
        'res.company', readonly=True, default=lambda self: self.env.user.company_id.id)
    employee_id = fields.Many2one("hr.employee", string="Employee",  tracking=True, required=1,
                                  default=lambda self: self.env.user.employee_id)
    user_id = fields.Many2one("res.users", related='employee_id.user_id')
    department_id = fields.Many2one("hr.department", string="Department", related='employee_id.department_id')
    job_id = fields.Many2one('hr.job', related='employee_id.job_id')
    name = fields.Char('Name')
    state = fields.Selection(string='State', selection=[
        ('draft', 'Draft'),
        ('officer', 'Officer Approved'),
        ('manager', 'Manager Approved'),
        ('active', 'Active'),
        ('deactive', 'Deactive'),
    ], default='draft', tracking=True )

    limit = fields.Float('Limit', default=_get_limit, tracking=True)
    over_limit = fields.Boolean('Over Limit')
    manay_petty = fields.Boolean('To many petty')

    petty_account_id = fields.Many2one(comodel_name='account.account', string='Petty Cash Account',
                                       default=_get_petty_account_id, tracking=True )
    purchase_journal_id = fields.Many2one(comodel_name='account.journal', string='Purchase Journal',
                                          default=_get_purchase_journal_id, tracking=True )
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account',
                                          default=_get_analytic_account_id, tracking=True)


    @api.constrains('employee_id')
    def _check_employee(self):
        for record in self:
            accounts = self.search([('id', '!=', self.id), ('state', 'not in', ['draft', 'deactive'])])
            if accounts:
                raise ValidationError(_('Employee already have petty cash account!'))

    def action_officer_approve(self):
        self.state = 'officer'

    def action_manager_approve(self):
        self.state = 'manager'

    def action_active(self):
        self.state = 'active'

    def action_deactive(self):
        self.state = 'deactive'

    @api.model
    def create(self, vals):
        vals.update(
            {'name': self.env['ir.sequence'].next_by_code('petty.user')})
        return super(PettyUser, self).create(vals)

