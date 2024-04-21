# -*- coding: utf-8 -*-
{
    'name': "Plus Tech HR Attendance",
    'version': '15.0.0.0.0',
    'author': 'Plus Technology Team',
    'company': 'Plus Technology',
    'category': 'Human Resources/Attendance',
    'website': "www.plustech-it.com",
    'description': """Attendance Customization""",
    'summary': """Attendance Customization""",
    'external_dependencies': {'python': ['xlrd']},

    # any module necessary for this one to work correctly
    'depends': ['hr_attendance', 'plustech_hr_payroll'],

    # always loaded
    'data': [
        'views/working_schedule.xml',
        'views/hr_employee_view.xml',
    ],
    'license': 'LGPL-3',
}
