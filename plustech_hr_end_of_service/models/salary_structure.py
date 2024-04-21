from odoo import fields, models, api, _


class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    @api.model
    def _get_default_rule_ids(self):
        result = super(HrPayrollStructure, self)._get_default_rule_ids()
        result += [(0, 0, {
            'name': _('EOS Provisions'),
            'sequence': 17,
            'code': 'EOSPROV',
            'category_id': self.env.ref('plustech_hr_payroll.provisions').id,
            'condition_select': 'none',
            'amount_select': 'code',
            'amount_python_compute': 'result = employee.cal_eos_provisions(payslip)',
        })
                   ]

        return result

    rule_ids = fields.One2many(
        'hr.salary.rule', 'struct_id',
        string='Salary Rules', default=_get_default_rule_ids)
