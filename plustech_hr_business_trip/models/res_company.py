# -*- coding: utf-8 -*-

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    def _domain_product_company(self):
        company = self.env.company
        return ['|', ('company_id', '=', False), ('company_id', '=', company.id),('detailed_type', '=', 'service')]

    def _domain_company(self):
        company = self.env.company
        return ['|', ('company_id', '=', False), ('company_id', '=', company.id)]


    deputation_ticket_product_id = fields.Many2one('product.product', string='Travel Ticket Product',
                                                   domain=_domain_product_company)
    deputation_allowance_product_id = fields.Many2one('product.product', string='Deputation Expense Product',
                                                      domain=_domain_product_company)
    deputation_analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account',
                                                     domain=_domain_company)
    deputation_leave_type_id = fields.Many2one('hr.leave.type', string='Deputation Leave', domain=_domain_company)
