# -*- coding: utf-8 -*-
{
    'name': "Plus Tech HR Attendance Transaction",
    'version': '15.0.0.0.0',
    'author': 'Plus Technology Team',
    'company': 'Plus Technology',
    'category': 'Human Resources/Attendance',
    'website': "www.plustech-it.com",
    'description': """Employees Attendance Transactions Management """,
    'summary': """Recording Attendance Transaction for Employees""",
    'depends': ['plustech_hr_contract',
                'hr',
                'hr_payroll',
                'plustech_hr_attendance'],
    'data': [
        'security/ir.model.access.csv',
        'security/hr_attendance_transaction_security.xml',
        'reports/monthly_attendance_report.xml',
        'reports/report_action.xml',
        'wizards/transaction_generate_wizard_views.xml',
        'wizards/attendance_report_wizard.xml',
        'data/data.xml',
        'data/payroll_rule_data.xml',
        'views/hr_attendance_transaction_view.xml',
        'views/exception_request_view.xml',
        'views/hr_payslip.xml',
        'views/hr_employee_shift_view.xml',
        'views/hr_allowance_type.xml',
        'views/hr_leave_type.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'plustech_hr_attendance_transaction/static/src/js/transaction_generate.js',
        ],
        'web.assets_qweb': [
            'plustech_hr_attendance_transaction/static/src/xml/transaction_generate.xml',
        ],
    },

    'license': 'OPL-1',
    'demo': [
    ],
}
