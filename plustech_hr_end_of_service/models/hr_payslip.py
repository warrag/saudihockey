# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    eos_id = fields.Many2one('end.of.service.reward', string='EOS Request')
    gross_wage = fields.Monetary(compute='_compute_gross_salary')
    payslip_type = fields.Selection(selection_add=[('eos', 'End Of Service')])

    def action_payslip_done(self):
        result = super(HrPayslip, self).action_payslip_done()
        if self.eos_id:
            self.eos_id.write({'state': 'paid'})
        return result

    def _compute_gross_salary(self):
        line_values = (self._origin)._get_line_values(['GROSS'])
        for payslip in self:
            payslip.gross_wage = line_values['GROSS'][payslip._origin.id]['total']


