from odoo import fields, models, api


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    violation_ded = fields.Float(string='Violation Month Deduction', compute='compute_violation_ded')
    penalty_ids = fields.One2many('hr.punishment', 'payslip_id', string="Penalties")

    @api.depends('employee_id', 'date_from', 'date_to')
    def compute_violation_ded(self):
        total_ded = 0.0
        for rec in self:
            violation_ded = self.env['hr.punishment'].search(
                [('employee_id', '=', rec.employee_id.id), ('applied_date', '>=', rec.date_from),
                 ('applied_date', '<=', rec.date_to), ('state', '<=', 'done'), '|',
                 ('applied_date', '>=', rec.date_from), ('remaining_amount', '>', 0)])
            if violation_ded:
                deduct_amount = ((self.contract_id.monthly_yearly_costs / 30) * 5)
                for ded in violation_ded:
                    if ded.remaining_amount <= deduct_amount:
                        total_ded += ded.ded_amount
                        deduct_amount -= deduct_amount
                        ded.payslip_id = self.id
                    elif ded.remaining_amount > deduct_amount:
                        total_ded += deduct_amount
                        ded.payslip_id = self.id
                        deduct_amount -= deduct_amount
            rec.violation_ded = total_ded

    def action_payslip_done(self):
        result = super(HrPayslip, self).action_payslip_done()
        for rec in self:
            if rec.penalty_ids:
                deduct_amount = ((self.contract_id.monthly_yearly_costs / 30) * 5)
                for ded in rec.penalty_ids:
                    if ded.remaining_amount <= deduct_amount:
                        ded.deducted_amount += ded.ded_amount
                        deduct_amount -= deduct_amount
                    elif ded.remaining_amount > deduct_amount:
                        ded.deducted_amount += deduct_amount
                        deduct_amount -= deduct_amount
        return result

