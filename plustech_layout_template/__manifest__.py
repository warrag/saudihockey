# -*- coding: utf-8 -*-

{
    'name': 'PlusTech Layout Templates',
    'version': '15.0.0.0',
    'category': 'Tools',
    'author': 'PlusTech',
    'depends': ['web', 'base'],
    'data': [
        "security/security.xml",
        "views/plustech_layout_template.xml",
        "views/res_company.xml",
    ],
    'demo': [],
    'test': [],
    'assets': {
        'web.report_assets_common': [
            '/invoice_templates/static/description/src/css/style.css',
        ],
    },
    'installable': True,
    'auto_install': False,
    "images": ['static/description/Banner.png'],
}
