{
    'name': "Plus Tech HR Work Initiation",
    'version': '15.0.0.0.0',
    'author': 'Plus Technology Team',
    'company': 'Plus Technology',
    'category': 'Human Resources/Work Initiation',
    'website': "www.plustech-it.com",
    'summary': """employee work initiation""",
    'description': """employee join work approval""",
    'depends': ['plustech_hr_employee', 'plustech_hr_leave', 'plustech_layout_template'],
    'data': [
        'security/hr_security.xml',
        'security/ir.model.access.csv',
        'data/work_initiation_sequence.xml',
        'views/work_initiation.xml',
        'views/hr_duty_commencement_type_views.xml',
        'reports/work_initiation_pdf.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
# -*- coding: utf-8 -*-

