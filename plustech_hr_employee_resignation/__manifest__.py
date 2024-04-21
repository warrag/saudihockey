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
    'name': 'Plus Tech HR Employee Resignation',
    'version': '15.0.0.0.0',
    'author': 'Plus Technology Team',
    'company': 'Plus Technology',
    'category': 'Human Resources',
    'website': "www.plustech-it.com",
    'description': """employees resignation management""",
    'summary': """""",
    'depends': ['plustech_hr_employee','plustech_hr_end_of_service'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/resignation_sequence.xml',
        'wizard/set_notice_period_wizard.xml',
        'views/resignation_view.xml',
    ],
    'sequence': 21,
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
