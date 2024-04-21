# -*- coding: utf-8 -*-

{
    'name': 'Plus Tech Announcements',
    'version': '15.0.0.0.0',
    'author': 'Plus Technology Team',
    'company': 'Plus Technology',
    'category': 'Human Resources',
    'website': "www.plustech-it.com",
    'summary': """Managing Official Announcements""",
    'description': """This module helps you to manage hr official announcements""",
    'depends': ['base', 'hr','mail'],
    'data': [
        'security/ir.model.access.csv',
        'security/reward_security.xml',
        'views/hr_announcement_view.xml',
    ],
    'demo': ['data/demo_data.xml'],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
