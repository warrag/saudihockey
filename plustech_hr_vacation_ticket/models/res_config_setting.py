# -*- coding: utf-8 -*-

from odoo import models, fields, api



class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'


    default_expense_account = fields.Many2one('account.account', string='Travel Expense Account',default_model='hr.leave',
                                             config_parameter='plustech_hr_vacation_ticket.default_expense_account' )

    desver_ticket_after = fields.Integer(string='Deserv Ticket After',default_model='hr.leave',default=11,
                                        config_parameter='plustech_hr_vacation_ticket.desver_ticket_after')
    not_deserve_ticket_after = fields.Integer(string='Not Deserve Ticket After', default_model='hr.leave',default=12,
                                        config_parameter='plustech_hr_vacation_ticket.not_deserve_ticket_after')
    tickets_analytic_account_id = fields.Many2one('account.analytic.account',string='Analtyic Account',default_model='account.analytic.account',
                                                    config_parameter='plustech_hr_vacation_ticket.tickets_analytic_account_id')

    def set_values(self):

        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('travel_expense_account', self.default_expense_account.id)
        self.env['ir.config_parameter'].sudo().set_param('desver_ticket_after', self.desver_ticket_after)
        self.env['ir.config_parameter'].sudo().set_param('not_deserve_ticket_after', self.not_deserve_ticket_after)
        self.env['ir.config_parameter'].sudo().set_param('tickets_analytic_account_id', self.tickets_analytic_account_id.id)



    @api.model
    def get_values(self):

        res = super(ResConfigSettings, self).get_values()
        res.update(

            default_expense_account=int(self.env['ir.config_parameter'].sudo().get_param('travel_expense_account',)),
            desver_ticket_after = self.env['ir.config_parameter'].sudo().get_param('desver_ticket_after'),
            not_deserve_ticket_after=int(self.env['ir.config_parameter'].sudo().get_param('not_deserve_ticket_after',)),
            # tickets_analytic_account_id = int(self.env['ir.config_parameter'].sudo().get_param('tickets_analytic_account_id',)),
        )

        return res
