from odoo import fields, models, api


class BankReportWizard(models.TransientModel):
    _name = 'payroll.bank.report'
    _description = 'Bank Report Wizard'

    report_type = fields.Many2one('ir.actions.report', string='Report Template',
                                  domain=[('model', '=', 'hr.payslip.run')])

    def action_print_excel(self):
        data = {'report_type': self.report_type}
        return self.report_type.report_action(self, data=data)
