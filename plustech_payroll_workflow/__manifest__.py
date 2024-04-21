# -*- coding: utf-8 -*-

{
    'name': 'Plus Tech HR Payroll Workflow',
    'version': '15.0.0.0.0',
    'author': 'Plus Technology Team',
    'company': 'Plus Technology',
    'category': 'Human Resources/Payroll',
    'website': "www.plustech-it.com",
    'description': """payslip batch workflow""",
    'summary': """payslip batch dynamic approvals""",
    'depends': ['base', 'plustech_hr_payroll'],
    'data': [
        'security/payroll_security.xml',
        'security/ir.model.access.csv',
        'views/hr_payslip_batch.xml',
        'views/payslip_batch_stage.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
