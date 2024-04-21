# -*- coding: utf-8 -*-

{
    'name': 'Plus Tech Employee Documents',
    'version': '15.0.0.0.0',
    'author': 'Plus Technology Team',
    'company': 'Plus Technology',
    'category': 'Human Resources/Letters',
    'website': "www.plustech-it.com",
    'description': """Manages Employee Related Documents with Expiry Notifications.""",
    'summary': """Manages Employee Documents With Expiry Notifications.""",
    'depends': ['base', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/employee_document_view.xml',
        'views/document_type_view.xml',
        'views/hr_document_template.xml',
    ],
    'demo': ['data/demo_data.xml'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
