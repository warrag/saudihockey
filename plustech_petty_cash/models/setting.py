# -*- coding: utf-8 -*-

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    def _get_default_transfer_account_id(self):
        return self.env.user.company_id.transfer_account_id.id

    petty_journal_id = fields.Many2one(comodel_name='account.journal', string='Petty Journal',
                                       domain="[('type','=','general')]")
    payment_journal_id = fields.Many2one(comodel_name='account.journal', string='Payment Journal',
                                         domain="[('type','in', ['cash', 'bank'])]")
    purchase_journal_id = fields.Many2one(comodel_name='account.journal', string=' Purchase Journal',
                                          domain="[('type','=','purchase')]")
    petty_account_id = fields.Many2one(
        comodel_name='account.account', string=' Petty Cash Account')

    petty_transfer_account_id = fields.Many2one(comodel_name='account.account', string='Internal Transfer Account',
                                                default=_get_default_transfer_account_id)
    petty_analytic_account_id = fields.Many2one(
        'account.analytic.account', string='Analytic Account')
    limit = fields.Float(string='Default Limit')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    petty_journal_id = fields.Many2one(comodel_name='account.journal', related="company_id.petty_journal_id",
                                       readonly=False,
                                       domain="[('type','=','general')]", default_model="res.company")
    payment_journal_id = fields.Many2one(related="company_id.payment_journal_id", readonly=False,
                                         domain="[('type','in', ['cash', 'bank'])]", default_model="res.company")
    purchase_journal_id = fields.Many2one(related="company_id.purchase_journal_id", readonly=False,
                                          default_model="res.company")
    petty_account_id = fields.Many2one(related="company_id.petty_account_id", readonly=False,
                                       default_model="res.company")
    petty_transfer_account_id = fields.Many2one(related="company_id.petty_transfer_account_id", readonly=False,
                                                default_model="res.company")
    petty_analytic_account_id = fields.Many2one(related="company_id.petty_analytic_account_id", readonly=False,
                                                default_model="res.company")
    limit = fields.Float(string='Default Limit', readonly=False,
                         related="company_id.limit")
