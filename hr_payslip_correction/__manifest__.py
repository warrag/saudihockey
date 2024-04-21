# -*- coding: utf-8 -*-
{ 
    'name': "Hr Payslip correction",
    'summary': """
        Hr Payslip correction""",
    'description': """
        Hr Payslip correction
    """,
    'author': "Magdy,TeleNoc",
    'website': "https://telenoc.org",
    'category': 'hr',
    'version': '0.13',
    'depends': ['hr', 'hr_payroll'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/hr_payslip_correction.xml',
    ],
}
