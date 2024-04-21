from odoo import fields, models, api, _


class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    @api.model
    def _get_default_rule_ids(self):
        result = super(HrPayrollStructure, self)._get_default_rule_ids()
        result += [(0, 0, {
            'name': _('Loan'),
            'sequence': 11,
            'code': 'LO',
            'category_id': self.env.ref('hr_payroll.DED').id,
            'condition_select': 'none',
            'amount_select': 'code',
            'amount_python_compute': 'result = -payslip.total_paid',
        })
                   ]

        return result

    rule_ids = fields.One2many(
        'hr.salary.rule', 'struct_id',
        string='Salary Rules', default=_get_default_rule_ids)
