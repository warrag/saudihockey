# -*- coding: utf-8 -*-
{
    'name': "Plus Tech HR Employee Penalty",
    'version': '15.0.0.0.0',
    'author': 'Plus Technology Team',
    'company': 'Plus Technology',
    'category': 'Human Resources/Penalty',
    'website': "www.plustech-it.com",
    'description': """HR Employee Penalty management""",
    'summary': """Hr Penalty for employee
                Configure Penalty based on employee , by department wise
                Penalty Notification to employee in one click
                Penalty Deduction in Employee Payslip""",
    'depends': ['base', 'plustech_hr_contract', 'plustech_hr_payroll', 'plustech_hr_employee'],
    'data': [
        'security/violation_security.xml',
        'security/ir.model.access.csv',
        'views/punishment_views.xml',
        'views/penalty_view.xml',
        'data/payroll_rule_data.xml',
        'data/violations_data.xml',
        'data/employee_inform_mail_template.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
