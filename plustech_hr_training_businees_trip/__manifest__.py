# -*- coding: utf-8 -*-

{
    'name': "Plus Tech Training Trip",
    'version': '15.0.0.0.0',
    'author': 'Plus Technology Team',
    'company': 'Plus Technology',
    'category': 'Human Resources/Training',
    'website': "www.plustech-it.com",
    'description': """link training with business trip""",
    'summary': """link training with business trip""",
    'depends': ['plustech_hr_business_trip','plustech_employee_training'],
    'data': [
        'views/training_request.xml',
        'reports/training_request.xml'
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
