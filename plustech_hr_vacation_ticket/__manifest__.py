# -*- coding: utf-8 -*-

{
    'name': "Plus Tech HR Vacation Ticket",
    'version': '15.1.1',
    'author': 'Plus Technology Team',
    'company': 'Plus Technology',
    'category': 'Human Resources/TimeOff Tickets',
    'website': "www.plustech-it.com",
    'description': """HR Vacation management""",
    'summary': """Vacation Management,manages employee vacation""",
    'depends': ['account', 'plustech_hr_leave'],
    'data': [
        'security/hr_vacation_security.xml',
        'security/ir.model.access.csv',
        'data/hr_payslip_data.xml',
        'reports/leave_ticket.xml',
        'views/hr_employee_ticket.xml',
        'views/hr_vacation.xml',
        'views/hr_leave_type.xml',
        'views/res_config_settings_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'plustech_hr_vacation_ticket/static/src/css/main.css',
            #   'plustech_hr_vacation_ticket/static/src/js/main.js',
        ],

    },
    'images': [],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
