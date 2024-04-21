# -*- coding: utf-8 -*-
#################################################################################
# Author      : Plus Tech.
# Copyright(c): 2021-Present TechPlus IT Solutions.
# All Rights Reserved.
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <www.plustech.com/license>
#################################################################################
{
    'name': 'Plus Tech HR Contracts Report(XLS)',
    'version': '15.0.1',
    'author': 'Plus Technology Team',
    'company': 'Plus Technology',
    'category': 'Human Resources/Contracts',
    'website': "www.plustech-it.com",
    'description': """employees contracts report""",
    'summary': """print employees contract report excel""",
    'depends': ['plustech_hr_employee', 'plustech_hr_contract',
                'plustech_hr_payroll', 'report_xlsx'],
    'data': [
        'security/ir.model.access.csv',
        'reports/report_xls_action.xml',
        'wizard/hr_contracts_report_wizard_views.xml',
    ],
    'sequence': 21,
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
