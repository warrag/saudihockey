from odoo import models, fields, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    loan_account_id = fields.Many2one(
        'account.account', string="Loan Account")
    loan_journal_id = fields.Many2one(
        'account.journal', string="Loans Journal")
    treasury_account_id = fields.Many2one(
        'account.account', string="Treasury Account")
    analytic_account_id = fields.Many2one(
        'account.analytic.account', string="Analytic Account")


class AccConfig(models.TransientModel):
    _inherit = 'res.config.settings'

    default_loan_account_id = fields.Many2one(
        'account.account', string="Loan Account", related='company_id.loan_account_id', readonly=False, default_model="hr.loan")
    default_loan_journal_id = fields.Many2one(
        'account.journal', string="Loan Journal", related='company_id.loan_journal_id', readonly=False, default_model="hr.loan",
        domain=lambda self: "[('company_id', '=', company_id)]",)
    default_treasury_account_id = fields.Many2one(
        'account.account', string="Treasury Account", related='company_id.treasury_account_id', readonly=False, default_model="hr.loan")
    default_analytic_account_id = fields.Many2one(
        'account.analytic.account', string="Analytic Account", related='company_id.analytic_account_id', readonly=False, default_model="hr.loan")
