from odoo import fields, models


class TrainingTimeTable(models.Model):
    _name = 'training.time.table'
    _description = 'Training Time Table'

    course_id = fields.Many2one('course.schedule', required=True, ondelete='cascade', index=True, copy=False)
    date = fields.Date(string='Date')
    week_day = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ], 'Day of Week', required=True, index=True, )
    hours = fields.Float(string='Hours')
