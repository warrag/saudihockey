{
    'name': 'Multi Company Hide Any Menu For Any User',
    'version': '0.1',
    'author': 'FreelancerApps',
    'category': 'Tools',
    'depends': ['base'],
    'data': [
        'security/multi_company_menu_hide_security.xml',
        'security/ir.model.access.csv',
        'views/company_view.xml',
        'wizard/wiz_fill_user_hide_menu.xml'
    ],
    'images': ['static/description/multi_company_hide_any_menu_banner.png'],
    'live_test_url': 'https://youtu.be/hov0m73bOMA',
    'currency': 'USD',
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
}
