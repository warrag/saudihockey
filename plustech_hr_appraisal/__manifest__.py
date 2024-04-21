# -*- encoding: utf-8 -*-




{
    'name': 'Plus Tech HR Appraisals',
    'version': '15.1.0',
    'category': 'Human Resources/Appraisals',
    'sequence': 180,
    'summary': 'Assess your employees',
    'website': 'www.plustech-it.com',
    'depends': ['plustech_hr_employee', 'hr'],
    'description': """
Periodical Employees appraisal
==============================

By using this application you can maintain the motivational process by doing periodical appraisals of your employees performance. The regular assessment of human resources can benefit your people as well your organization.

An appraisal plan can be assigned to each employee. These plans define the frequency and the way you manage your periodic personal appraisal.

Key Features
------------
* Ability to create employee's appraisal(s).
* An appraisal can be created by an employee's manager or by HR Responsible	.
* The appraisal is done according to a plan in which deadline can be submitted.
* Manager and employee himself/herself receives email to perform a periodical appraisal.
""",
    "data": [
        'security/appraisal_security.xml',
        'security/ir.model.access.csv',
        'data/cron.xml',
        'views/hr_appraisal_template_views.xml',
        'views/hr_appraisal_appraisal_views.xml',
        'views/hr_appraisal_batch.xml',
        'views/hr_job.xml',
        'views/appraisal_history.xml',
        'views/settings.xml',
        'views/menus.xml',
        'data/ir_module_data.xml'
    ],
    "demo": [
    ],
    'installable': True,
    'application': True,
    'license': 'OPL-1',
    'assets': {
        'web.assets_common': [
            'plustech_hr_appraisal/static/src/css/my_css.css',
        ],

    }
}
