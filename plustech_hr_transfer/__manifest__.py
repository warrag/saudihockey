# -*- coding: utf-8 -*-

{
    "name": "Plus tech Hr Employee Transfer",
    "summary": "HR Employee Transfer",
    'description': """
                    - transfer employee between departments
                    'transfer employee between work locations
                """,
    'author': 'Plus Technology Team',
    'company': 'Plus Technology',
    'category': 'Human Resources/Employee Transfer',
    'website': "www.plustech-it.com",
    "version": "15.0.2.0",
    "license": "LGPL-3",
    "depends": [
        'hr_contract',
        "hr",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_department.xml",
        "views/hr_employee_transfer.xml",
        "views/employee_transfer_history.xml",
        "views/hr_employee.xml",
        "views/hr_work_location.xml",
    ],
    "installable": True,
}
