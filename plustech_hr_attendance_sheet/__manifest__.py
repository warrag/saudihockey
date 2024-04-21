# -*- coding: utf-8 -*-
{
    'name': "Plus Tech HR Attendance Sheet",
    'version': '15.0.0.0.0',
    'author': 'Plus Technology Team',
    'company': 'Plus Technology',
    'category': 'Human Resources/Attendance',
    'website': "www.plustech-it.com",
    'description': """Employees Attendance  Management """,
    'summary': """generate attendance report for payroll period""",
    'depends': ['plustech_hr_attendance_transaction'],
    'data': [
        'security/ir.model.access.csv',
        'security/hr_attendance_sheet_security.xml',
        'data/payroll_data.xml',
        'data/payroll_rule_data.xml',
        'views/hr_payslip.xml',
        'views/attendance_deduction_view.xml',
    ],

    'license': 'OPL-1',
    'demo': [
    ],
}
