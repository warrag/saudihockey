# -*- coding: utf-8 -*-

{
    "name": "Plus Tech Employee Request",
    "author": "Plus Technology Team",
    "version": "15.0.0",
    "summary": "employee request for item management"
    "materials and/or external services and keep track of such "
    "requirements.",
    "website": "www.plustech-it.com",
    "category": "Human Resources/Employee Requisition",
    "depends": ["product", "plustech_hr_employee", 'plustech_layout_template'],
    "data": [
        "security/employee_request.xml",
        "security/ir.model.access.csv",
        "data/employee_request_sequence.xml",
        "reports/report_employee_request.xml",
        "views/hr_employee_request_view.xml",
    ],    "license": "OPL-1",
    "installable": True,
    "application": True,
}
