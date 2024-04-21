# -*- coding: utf-8 -*-

{
    'name': "PlusTech HR Flight Ticket",
    'version': '15.1.1',
    'author': 'Plus Technology Team',
    'company': 'Plus Technology',
    'category': 'Human Resources',
    'website': "www.plustech-it.com",
    'description': """HR Vacation management""",
    'summary':  """
                    Vacation Management,manages employee vacation
                """,
    'depends': ['account', 'plustech_hr_leave', 'plustech_hr_employee', 'plustech_layout_template'],
    'data': [
        'security/hr_vacation_security.xml',
        'security/ir.model.access.csv',
        'data/hr_payslip_data.xml',
        'views/flight_ticket.xml',
        'wizard/flight_ticket.xml',
        'views/hr_vacation.xml',
        'views/hr_leave_type.xml',
        'views/res_config_settings_view.xml',
        'views/flight_class.xml',
        'views/flight_activity.xml',
        'views/res_partner.xml',
        'data/res_partner.xml',
        'data/flight_class.xml',
        'reports/flight_ticket.xml',

    ],
    'assets': {
        'web.assets_backend': [
            'plustech_hr_flight_ticket/static/src/css/main.css',
            #   'plustech_hr_flight_ticket/static/src/js/main.js',
        ],

    },
    'images': [],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
