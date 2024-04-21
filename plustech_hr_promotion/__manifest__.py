# -*- coding: utf-8 -*-
{
    'name': "Plus Tech HR Promotion",
    'version': '15.0.0.0.0',
    'author': 'Plus Technology Team',
    'company': 'Plus Technology',
    'category': 'Human Resources/Promotions',
    'website': "www.plustech-it.com",
    'description': """To Manage employee promotion process""",
    'summary': """employees promotion management""",
    'depends': ['plustech_hr_employee'],

    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/employee_promotion.xml',
        'views/promotion_stage.xml',
        'views/hr_employee.xml',
        'data/request_sequence.xml',
        'data/mail_template.xml',
        'data/cron.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
