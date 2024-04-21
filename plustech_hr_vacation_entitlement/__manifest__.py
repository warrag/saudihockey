# -*- coding: utf-8 -*-

{
    'name': "Plus Tech HR Vacation Entitlement",
    'version': '15.0.0.0.0',
    'author': 'Plus Technology Team',
    'company': 'Plus Technology',
    'category': 'Human Resources/Time Off',
    'website': "www.plustech-it.com",
    'description': """Vacation Entitlement Management""",
    'summary': """HR Vacation entitlement management""",
    'depends': ['account', 'plustech_hr_payroll', 'plustech_hr_leave'],
    'data': [
        'security/hr_vacation_security.xml',
        'security/ir.model.access.csv',
        'data/hr_payslip_data.xml',
        'data/hr_vacation_entitlement_sequence.xml',
        'views/hr_vacation_entitlement.xml',
        'views/hr_payslip.xml',

    ],

    'images': [],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
