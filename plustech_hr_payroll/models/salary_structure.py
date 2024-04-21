from odoo import fields, models, api, _


class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'
    _check_company_auto = True

    company_id = fields.Many2one(
        'res.company', string='Company', copy=False, required=True,
        default=lambda self: self.env.company)
    default_account_id = fields.Many2one('account.account', check_company=True, copy=False, ondelete='restrict',
                                         string='Default Account',
                                         domain="[('deprecated', '=', False), ('company_id', '=', company_id),"
                                                "('user_type_id.type', 'not in', ('receivable', 'payable'))]")

    @api.model
    def _get_default_rule_ids(self):
        result = super(HrPayrollStructure, self)._get_default_rule_ids()
        result += [(0, 0, {
            'name': _('Total Additions'),
            'sequence': 99,
            'code': 'TADD',
            'category_id': self.env.ref('plustech_hr_payroll.TOTAL').id,
            'condition_select': 'none',
            'amount_select': 'code',
            'amount_python_compute': 'result = categories.ALW',
        }),
                   (0, 0, {
                       'name': _('GOSI Contribution For Employee'),
                       'sequence': 99,
                       'code': 'GOSI',
                       'category_id': self.env.ref('hr_payroll.DED').id,
                       'condition_select': 'none',
                       'amount_select': 'code',
                       'amount_python_compute': 'result = -payslip.gosi_employee_deduction',
                   }),
                   (0, 0, {
                       'name': _('GOSI Company Contribution For Employee'),
                       'sequence': 99,
                       'code': 'GOSI_COMP',
                       'category_id': self.env.ref('hr_payroll.COMP').id,
                       'condition_select': 'none',
                       'amount_select': 'code',
                       'amount_python_compute': 'result = payslip.gosi_company_deduction',
                   }),
                   (0, 0, {
                       'name': _('Total Deductions'),
                       'sequence': 99,
                       'code': 'TDED',
                       'category_id': self.env.ref('plustech_hr_payroll.TOTAL').id,
                       'condition_select': 'none',
                       'amount_select': 'code',
                       'amount_python_compute': 'result =  categories.DED',
                   })
                   ]

        return result

    rule_ids = fields.One2many(
        'hr.salary.rule', 'struct_id',
        string='Salary Rules', default=_get_default_rule_ids)
