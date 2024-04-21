# -*- coding: utf-8 -*-
{
    'name': "Plus Tech Employee Expenses",
    'version': '15.0.0.0.0',
    'author': 'Plus Technology Team',
    'company': 'Plus Technology',
    'category': 'Human Resources/HR Expenses',
    'website': "www.plustech-it.com",
    'description': """Manage Employee expense""",
    'summary': """ register employee expenses.
                """,
    'depends': ['plustech_hr_employee'],
    'data': [
        # 'security/eos_security.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'data/ir_cron_job.xml',
        'views/hr_expense_views.xml',
        'views/hr_employee_cost_view.xml',
        'views/res_config.xml',
        'views/hr_expense_type_views.xml',
    ],

    'license': "LGPL-3",

    'installable': True,
    'application': False,
    'auto_install': False,

}
