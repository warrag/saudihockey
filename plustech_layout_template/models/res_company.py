
from datetime import date
from odoo import models, fields, api, _
import base64
from io import BytesIO

class ResCompany(models.Model):
    _inherit = "res.company"

    company_name = fields.Html('Name')
    report_footer_text = fields.Html(string='Footer Text')


    
