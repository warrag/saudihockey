from odoo import fields, models, api


class JobPositionCategory(models.Model):
    _name = 'job.position.category'
    _description = 'Job Position Category'

    name = fields.Char(translate=True)


class JobPosition(models.Model):
    _inherit = 'hr.job'

    category_id = fields.Many2one('job.position.category', string='Category', ondelete='restrict')
