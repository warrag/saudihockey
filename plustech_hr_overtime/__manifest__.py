# -*- coding: utf-8 -*-

{
    'name': 'Plus-Tech Hr Overtime',
    'version': '15.0.0.0.0',
    'author': 'Plus Technology Team',
    'company': 'Plus Technology',
    'category': 'Human Resources/Overtime',
    'website': "www.plustech-it.com",
    'description': """Manage Employee Overtime""",
    'summary': """Easy to manage employee overtime.
            The employee can create their own overtime request.
            The overtime request approve/reject by the manager.
            Managers can filter requests based on overtime types.
                """,
    'depends': [
        'plustech_hr_employee', 'hr_contract', 'plustech_hr_attendance', 'hr_holidays',
        'plustech_hr_payroll', 'plustech_hr_attendance_transaction'
    ],
    'pre_init_hook': 'pre_init_hook',
    'data': [
        'security/security_view.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/overtime_request_view.xml',
        'views/overtime_type.xml',
        'views/hr_contract.xml',
        'views/hr_payslip.xml',
        'views/res_config_settings_view.xml',
        'views/working_schedule.xml',
        'views/hr_attendance_transaction_view.xml',
    ],
    'images': [],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
