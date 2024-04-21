from odoo import fields, models, api


class HrJob(models.Model):
    _inherit = 'hr.job'

    appraisal_tmp_id = fields.Many2one('hr.appraisal.template', string="Appraisal Template")
