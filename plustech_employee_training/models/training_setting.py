# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    training_product_id = fields.Many2one('product.product', string="Product")
    training_analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account")


class AccConfig(models.TransientModel):
    _inherit = 'res.config.settings'

    training_product_id = fields.Many2one(string="Product",related='company_id.training_product_id', readonly=False)
    training_analytic_account_id = fields.Many2one(string="Analytic Account",
                                                   related='company_id.training_analytic_account_id',  readonly=False)


class CourseAgreementTemplate(models.Model):
    _name = 'course.agreement.template'
    _description = 'Course Agreement Template'

    agreement_content = fields.Html()
    reference = fields.Char(string='Code', size=5)
    name = fields.Char(string='Subject', translate=True)

    _sql_constraints = [
        ('agreement_reference_unique',
         'UNIQUE(reference)',
         _('Code Must be Unique')),
    ]


