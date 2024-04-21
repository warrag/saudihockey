# -*- coding: utf-8 -*-

{
    'name': "Plus Tech Employee's Training",
    'version': '15.0.0.0.0',
    'author': 'Plus Technology Team',
    'company': 'Plus Technology',
    'category': 'Human Resources/Training',
    'website': "www.plustech-it.com",
    'description': """Training Management""",
    'summary': """Manage employees training""",
    'depends': ['base', 'mail', 'plustech_hr_employee',
                'plustech_hr_payroll', 'plustech_hr_leave', 'plustech_layout_template'],
    'data': [

        'security/training_security.xml',
        'security/ir.model.access.csv',
        'data/salary_rule.xml',
        'data/request_sequence.xml',
        'data/hr_leave_type.xml',
        'views/views.xml',
        'views/agreement_view.xml',
        'views/sequence.xml',
        'views/training_settings_view.xml',
        'views/res_partner.xml',
        'views/training_request.xml',
        'views/training_employee.xml',
        'views/course_schedule.xml',
        'views/training_activity_view.xml',
        'reports/training_request.xml',
    ],

    'images': ['static/description/train.jpeg'],

    'demo': [
        'demo/demo.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
