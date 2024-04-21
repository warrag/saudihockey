# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools import float_round


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def compute_ticket_allowance(self, payslip=False):
        value = 0.0
        if payslip:
            domain = [('state', '=', 'confirmed'), ('employee_id', '=', payslip['employee_id'].id),
                      ('paid_for_employee', '=', True),
                      ('payslip_paid', '=', False), ('date_start', '>=', payslip['date_from'])]
            ticket_id = self.env['hr.flight.ticket'].search(domain, limit=1)
            value = ticket_id.ticket_fare
            value = float_round(value,
                                precision_digits=self.env['decimal.precision'].precision_get('Payroll'))
        return value

    def action_payslip_done(self):
        """
        function used for marking paid overtime
        request.

        """
        for rec in self:
            domain = [('state', '=', 'confirmed'), ('employee_id', '=', rec.employee_id.id),
                      ('paid_for_employee', '=', True),
                      ('payslip_paid', '=', False), ('date_start', '>=', rec.date_from)]
            ticket_id = self.env['hr.flight.ticket'].search(domain, limit=1)
            if ticket_id:
                ticket_id.write({'payslip_paid': True, 'state': 'paid'})
        return super(HrPayslip, self).action_payslip_done()
