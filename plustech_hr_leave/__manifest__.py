{
    'name': "Plus Tech Hr Leaves",
    'version': '15.1.0',
    'author': 'Plus Technology Team',
    'company': 'Plus Technology',
    'category': 'Human Resources/Time Off',
    'website': "www.plustech-it.com",
    'description': """Manage Employee Leaves""",
    'summary': """timeoff localization.
                """,
    'depends': ['plustech_hr_employee','hr_payroll_holidays','plustech_hr_contract', 'hr_holidays', 'hr_contract_salary_holidays'],
    'assets': {
        'web.assets_backend':[
            'plustech_hr_leave/static/src/js/time_off_calendar_employee.js',
            'plustech_hr_leave/static/src/js/leave_balance_at_date.js',
            'plustech_hr_leave/static/src/js/leave_stats_widget.js',
        ],
        'web.assets_qweb': [
            'plustech_hr_leave/static/src/xml/leave_balance_report.xml'
        ]
    },
    'data': [
        'security/leaves_security.xml',
        'security/ir.model.access.csv',
        'data/update_leave_balance.xml',
        'data/hr_holidays_data.xml',
        'data/sick_leave_rules_data.xml',
        'data/digits.xml',
        'wizard/leave_refuse_wizard.xml',
        'wizard/leave_balance_history.xml',
        'wizard/leave_cut_wizard.xml',
        'views/ir_config_setting.xml',
        'views/hr_employee.xml',
        'views/hr_contract_view.xml',
        'views/hr_leave.xml',
        'views/hr_permission.xml',
        'views/hr_leave_type.xml',
        'views/hr_leave_balance.xml',
        'views/leave_accrual_plan.xml',
        'views/sick_leaves.xml',
        'views/hr_leave_allocation.xml',
        'views/leave_multi_approval.xml',
        'report/leave_report_pdf.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
# -*- coding: utf-8 -*-
