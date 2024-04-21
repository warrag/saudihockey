# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    deputation_ticket_product_id = fields.Many2one('product.product', string='Travel Ticket Product',
                                                   related="company_id.deputation_ticket_product_id",
                                                   domain=[('detailed_type', '=', 'service')], readonly=False)
    deputation_allowance_product_id = fields.Many2one('product.product', string='Deputation Expense Product',
                                                      related="company_id.deputation_allowance_product_id",
                                                      domain=[('detailed_type', '=', 'service')], readonly=False)
    deputation_analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account',
                                                     readonly=False,
                                                     related="company_id.deputation_analytic_account_id",
                                                     )
    leave_type_id = fields.Many2one('hr.leave.type', string='Deputation Leave',
                                    default=lambda self: self.env.ref(
                                        'plustech_hr_business_trip.holiday_status_business_trip_leave'),
                                    related="company_id.deputation_leave_type_id", readonly=False
                                    )
