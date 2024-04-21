# -*- coding: utf-8 -*-

from odoo import models, fields, api


class EndServiceReason(models.Model):
    _name = 'end.service.reason'
    _description = 'EOS Reason'
    _check_company_auto = True

    name = fields.Char(string="Name", required=True, translate=True)
    reason_type = fields.Selection(
        [('termination', 'Termination'), ('resign', 'Resignation'), ('end', 'End of Contract')])
    journal_id = fields.Many2one('account.journal', string='Default Journal', domain=[('type', 'in', ['cash', 'bank'])])
    rule_id = fields.One2many('eos.rules', 'reason_id', string='EOS Rules')
    includ_allowance = fields.Boolean(string='Include all Allowance?', default=True)
    allowance_ids = fields.Many2many('employee.allowance.type', string='Allowance',
                                     domain=[('salary_rule_id.category_id.code', '=', 'ALW')])
    provision_calculatation = fields.Boolean(string='Use in Payslip',
                                             help="Use This Rule to calculate eos provisions in payslip")
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company)
    include_compensation = fields.Boolean(string='Include Compensation')
    min_months_compensation = fields.Integer(string="Minimum Month's To Skip Remaining Period")

    @api.onchange('rule_id')
    def _rule_no(self):
        no = 1
        for line in self.rule_id:
            line.no = no
            no += 1


class EosRules(models.Model):
    _name = 'eos.rules'
    _description = 'EOS Rules'

    no = fields.Integer(string='No#', readonly=True)
    period_from = fields.Integer(string='Period From(Years)', required=True)
    period_to = fields.Integer(string='Period To(Years)', required=True)
    eos_award = fields.Float(string='EOS Award(Month)', required=True)
    reason_id = fields.Many2one('end.service.reason')
    calculate_factor = fields.Float(string='Calculation Factor', required=True, digits='EOS Rules')
