# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Plus-Tech Payslip Batch Report',
    'category': 'Payroll',
    'sequence': 906,
    'summary': 'Summary of all payslips as a pivot table',
    'description': "Create Payroll reports based on pivot view engine.",
    'images': ['static/images/main_thumb.png'],
    'author': 'PlusTech',
    'version': '1.0',
    'license': 'AGPL-3',  # For Odoo13
    'application': False,
    'installable': True,
    'depends': [
        'hr_payroll',
    ],
    'data': [
        'security/security_view.xml',
        'views/pivot_views.xml',
        'views/hr_payslip_batch.xml',
        'views/menus.xml',
    ],
}
