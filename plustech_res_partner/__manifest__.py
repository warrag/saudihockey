# -*- coding: utf-8 -*-
{
    'name': "Partner Custom Fields",

    'summary': """
        Enables to search partners in quotation, sale, purchase, invoice etc by the phone and mobile numbers""",

    'description': """
        Enables to search partners in quotation, sale, purchase, invoice etc by the phone and mobile numbers
    """,

    'category': 'Uncategorized',
    'version': '15.0.1.0.0',

    'depends': ['base'],
    'data': [
        'views/res_partner_views.xml'
    ],
    'application': True,
    'installable': True,
}
