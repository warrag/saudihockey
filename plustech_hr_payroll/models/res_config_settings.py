from odoo import models, fields, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    payslip_payment_journal_id = fields.Many2one(
        'account.journal', string="Payment Journal")

    payment_generation_method = fields.Selection(
        selection=[('batch', 'Batch'), ('separate', 'Separate')],
        string='Payment Generation Method', default='batch'
    )
    payslip_entry_generation = fields.Selection([
        ('grouping', 'Grouping By Account'),
        ('separate', 'Grouping By Employee')],
        default='grouping', string='Payroll Journal Items')
    max_salary_for_gosi = fields.Float('Max Salary For GOSI', default=45000)


class BatchPaymentConfig(models.TransientModel):
    _inherit = 'res.config.settings'

    default_journal_id = fields.Many2one(
        'account.journal', string="Payment Journal", related='company_id.payslip_payment_journal_id',
        domain=[('type', 'in', ('bank', 'cash'))], readonly=False, default_model="emp.payslip.payment")
    default_payment_generation_method = fields.Selection(
        related='company_id.payment_generation_method',
        string='Payment Generation Method', readonly=False, default='batch', default_model="emp.payslip.payment")
    payslip_entry_generation = fields.Selection(related='company_id.payslip_entry_generation', string='Payroll Journal Items', readonly=False)
    max_salary_for_gosi = fields.Float(related='company_id.max_salary_for_gosi', string='Max Salary For GOSI', readonly=False)
