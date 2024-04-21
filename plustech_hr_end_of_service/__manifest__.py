# -*- coding: utf-8 -*-
{
    'name': "Plus Tech End of Services Reward",
    'version': '15.0.0.0.0',
    'author': 'Plus Technology Team',
    'company': 'Plus Technology',
    'category': 'Human Resources/End Of Service',
    'website': "www.plustech-it.com",
    'description': """Manage Employee End of service""",
    'summary': """calculation of end of services reward.
                """,
    'depends': ['base', 'plustech_hr_payroll', 'plustech_hr_employee', 'plustech_hr_contract',
                'plustech_hr_loan', 'plustech_hr_custody',
                'plustech_hr_attendance_transaction'],
    'data': [
        'security/eos_security.xml',
        'security/ir.model.access.csv',
        'data/salary_rule.xml',
        'data/eos_sequence.xml',
        'data/eos_reason_data.xml',
        'data/calculate_factor_digits.xml',
        'views/hr_employee_view.xml',
        'views/end_of_service.xml',
        'views/res_config.xml',
        'views/eos_reason.xml',
        'views/hr_eos_other_input_views.xml',
        'views/payment_view.xml',
        'views/loans_view.xml',
        'reports/eos_clearance_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'plustech_hr_end_of_service/static/src/css/style.css',
        ],

    },
    'license': "LGPL-3",

    'installable': True,
    'application': False,
    'auto_install': False,

}
