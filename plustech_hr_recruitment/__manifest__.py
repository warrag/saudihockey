{
    'name': "Plus Tech Employee Recruitment",
    'version': '15.0.0.0.0',
    'author': 'Plus Technology Team',
    'company': 'Plus Technology',
    'category': 'Human Resources/Recruitment',
    'website': "www.plustech-it.com",
    'summary': """hr recruitment extension""",
    'description': """customize recruitment module to add:
       1. Recruitment plan by department""",
    'depends': ['base', 'plustech_hr_employee', 'hr_recruitment', 'hr_skills'],
    'data': [
        'security/ir.model.access.csv',
        'security/job_request.xml',
        # 'data/recruitment_plan_sequence.xml',
        'data/job_request_seq.xml',
        # 'data/recruitment_data.xml',
        # 'views/recruitment_plan.xml',
        'views/job_request.xml',
        'views/hr_applicant.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
# -*- coding: utf-8 -*-

