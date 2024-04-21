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
    'name': 'Plus Tech HR Contract',
    'version': '15.0.0.0.0',
    'author': 'Plus Technology Team',
    'company': 'Plus Technology',
    'category': 'Human Resources/Contracts',
    'website': "www.plustech-it.com",
    'description': """employees contract management""",
    'summary': """employees contract localization""",
    'depends': ['base', 'plustech_hr_employee', 'hr_contract', 'hr_contract_salary','hr_work_entry_contract_enterprise'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/server_action.xml',
        'data/contract_type.xml',
        'views/hr_contract_type.xml',
        'views/hr_contract.xml',
        'views/hr_contract_template.xml',
        'reports/print_contract.xml',
        'data/contract_template_base.xml',
        'views/res_company.xml',
        'views/res_config_setting.xml',
    ],
    'sequence': 21,
    'demo': [],
    'pre_init_hook': 'pre_init_contract',
    'assets': {
        'web.report_assets_common': [
            'plustech_hr_contract/static/src/css/style.css'
        ],
        'web.report_assets_pdf': [
            'plustech_hr_contract/static/src/css/style.css'
        ],
        'web.assets_backend': [
            'plustech_hr_contract/static/src/css/style.css',
        ],
    },
    'images': [],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
