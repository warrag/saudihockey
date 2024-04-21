{
    'name': "Plus Tech Delegation",
    'version': '15.1.0',
    'author': 'Plus Technology Team',
    'company': 'Plus Technology',
    'category': 'Human Resources/Delegation',
    'website': "www.plustech-it.com",
    'summary': """employee delegation for leave""",
    'description': """employee delegation for leave""",
    'depends': ['plustech_hr_leave'],
    'data': [
        'security/ir.model.access.csv',
        'data/delegation_sequence.xml',
        'views/hr_employee_delegation.xml',
        'views/hr_leave_type.xml',
        'views/hr_leave.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
# -*- coding: utf-8 -*-

