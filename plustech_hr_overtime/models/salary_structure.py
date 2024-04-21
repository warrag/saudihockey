from odoo import fields, models, api, _


class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    @api.model
    def _get_default_rule_ids(self):
        result = super(HrPayrollStructure, self)._get_default_rule_ids()
        result += [(0, 0, {
            'name': _('Overtime'),
            'sequence': 100,
            'code': 'OT100',
            'category_id': self.env.ref('hr_payroll.ALW').id,
            'condition_select': 'python',
            'amount_select': 'code',
            'condition_python': 'result = inputs.OT100',
            'amount_python_compute': 'result = inputs.OT100.amount',
        })
                   ]

        return result

    rule_ids = fields.One2many(
        'hr.salary.rule', 'struct_id',
        string='Salary Rules', default=_get_default_rule_ids)
