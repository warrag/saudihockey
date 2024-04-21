{
    'name': 'Hide Any Field',
    'version': '1.0.1',
    'author': 'Hassan',
    'category': 'Tools',
    'depends': ['base'],
    'summary': 'Hide Any Field',
    'description': """
Hide/Invisible Any  Field, From Any User
========================================================================================
Key features:
-------------
* Easy To Configure
* Hide, Set Readonly Any Field From Any Group And Its Users Configuration On Models Form View.
""",
    'data': [
        'views/res_company_view.xml',
        'security/ir.model.access.csv',
    ],
    'images': [],
   
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
}
