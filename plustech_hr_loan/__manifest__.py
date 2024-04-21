# -*- coding: utf-8 -*-
#################################################################################
# Author      : Plus Tech.
# Copyright(c): 2021-Present TechPlus IT Solutions.
# All Rights Reserved.
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <www.plustech.com/license>
#################################################################################
{
    'name': 'Plus-Tech HR Loan',
    'version': '15.0.0.0.0',
    'author': 'Plus Technology Team',
    'company': 'Plus Technology',
    'category': 'Human Resources/Contracts',
    'website': "www.plustech-it.com",
    'description': """Employee Loan  management""",
    'summary': """Odoo App for Employee Loan Integration HR Payroll""",
    'depends': ['base', 'hr_payroll', 'plustech_hr_payroll',
                'plustech_hr_employee', 'account', ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'sequence/loan_sequence.xml',
        'views/hr_loan.xml',
        'views/hr_loan_acc.xml',
        'views/hr_loan_config.xml',
        'views/payslip.xml',
        'views/hr_employee.xml',
        'views/employee_other_loans.xml',
        'views/hr_loan_type.xml',
        'views/loan_policy.xml',
        'views/hr_skip_installment_view.xml',
        'data/salaey_rules.xml',
        'data/mail_templates.xml',
        'reports/print_loan.xml',

    ],
    'demo': [],
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}
