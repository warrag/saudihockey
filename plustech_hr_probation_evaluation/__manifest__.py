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
    'name': 'Plus Tech HR Probation Evaluation',
    'version': '15.1.0',
    'author': 'Plus Technology Team',
    'company': 'Plus Technology',
    'category': 'Human Resources',
    'website': "www.plustech-it.com",
    'description': """probation evaluation management""",
    'summary': """trial period evaluation""",
    'depends': ['plustech_hr_employee', 'hr_contract'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/cron_jobs.xml',
        'data/mail_activity.xml',
        'views/hr_contract.xml',
        'views/employee_probation_evaluation.xml',

    ],
    'sequence': 21,
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
