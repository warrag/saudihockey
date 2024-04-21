# -*- coding: utf-8 -*-
# This file is part of OpenERP. The COPYRIGHT file at the top level of
{
    'name': 'Plus Tech Payroll Excel Report',
    'version': '15.0.0.0.0',
    'author': 'Plus Technology Team',
    'company': 'Plus Technology',
    'category': 'Human Resources',
    'website': "www.plustech-it.com",
    'summary': """Excel sheet for payslips""",
    'description': """Excel sheet for payslips""",
    'depends': [
        'plustech_hr_payroll', 'base', 'report_xlsx',
    ],
    'data': [
        'security/ir.model.access.csv',
        'reports/report_xls_action.xml',
        'wizard/payroll_bank_report.xml',
        'views/payslip_batch.xml',
    ],
    'images': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',

}
# this module contains the full copyright notices and license terms.
