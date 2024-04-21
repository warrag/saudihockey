# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class WorkingSchedule(models.Model):
    _inherit = 'resource.calendar.attendance'
    check_in_start = fields.Float(string='Check-In Start Time', default=7.0, required=True,
                                  help='Check-In Start Time (24 Hours e.g 13, 16)')
    check_in_start_str = fields.Char(string='Check-In Start', compute='compute_char_values', store=True)
    check_in = fields.Float(string='Check-In', default=8.0, required=True,
                            help='Check-In Time (24 Hours e.g 13, 16)')
    check_in_str = fields.Char(string='Check-In', compute='compute_char_values', store=True)
    check_out_start = fields.Float(string='Check-out Start Time', default=15.0, required=True,
                                   help='Check-Out Start Time (24 Hours e.g 13, 16)')
    check_out_start_str = fields.Char(string='Check-Out Start', compute='compute_char_values', store=True)
    check_out = fields.Float(string='Check-out', default=16.0, required=True,
                             help='Check-Out Time (24 Hours e.g 16, 18)')
    check_out_str = fields.Char(string='Check-Out', compute='compute_char_values', store=True)
    check_in_end = fields.Float(string='Check-In End Time', default=9.0, required=True,
                                help='Check-Out End Time (24 Hours e.g 18, 20)'
                                )
    check_in_end_str = fields.Char(string='Check-In End', compute='compute_char_values', store=True)
    check_out_end_str = fields.Char(string='Check-Out End', compute='compute_char_values', store=True)
    check_out_end = fields.Float(string='Check-Out End Time', default=17, required=True)
    is_weekend = fields.Boolean(string='Is Weekend')

    @api.constrains('check_in_start', 'hour_from', 'check_in_end', 'check_out_start', 'hour_to', 'check_out_end')
    def attendance_ids_cons(self):
        for rec in self:
            if rec.check_in_start > rec.hour_from:
                raise UserError('Check-In Start Must Be Less Than Check-In')
            if rec.hour_from > rec.check_in_end:
                raise UserError('Check-In Must Be Less Than Check-In End')
            if rec.check_in_start > rec.check_in_end:
                raise UserError('Check-In Start Must Be Less Than Check-In End')
            if rec.check_out_start > rec.hour_to:
                raise UserError('Check-Out Start Must Be Less Than Check-Out')
            if rec.hour_to > rec.check_out_end:
                raise UserError('Check-Out Must Be Less Than Check-Out End')
            if rec.check_out_start > rec.check_out_end:
                raise UserError('Check-Out Start Must Be Less Than Check-Out End')

    @api.depends('check_in', 'check_out', 'check_in_start', 'check_out_start', 'check_in_end',
                 'check_out_end', 'check_out_start')
    def compute_char_values(self):
        for rec in self:
            hour = int(rec.hour_from)
            minute = int((rec.hour_from - hour) * 60)
            hour_out = int(rec.hour_to)
            minute_out = int((rec.hour_to - hour_out) * 60)
            start_hour_in = int(rec.check_in_start)
            start_minute_in = int((rec.check_in_start - start_hour_in) * 60)
            start_hour_out = int(rec.check_out_start)
            start_minute_out = int((rec.check_out_start - start_hour_out) * 60)
            end_hour_in = int(rec.check_in_end)
            end_minute_in = int((rec.check_in_end - end_hour_in) * 60)
            end_hour_out = int(rec.check_out_end)
            end_minute_out = int((rec.check_out_end - end_hour_out) * 60)
            rec.check_in_start_str = str(start_hour_in) + ':' + str(start_minute_in) + ':00'
            rec.check_in_str = str(hour) + ':' + str(minute) + ':00'
            rec.check_in_end_str = str(end_hour_in) + ':' + str(end_minute_in) + ':00'
            rec.check_out_start_str = str(start_hour_out) + ':' + str(start_minute_out) + ':00'
            rec.check_out_str = str(hour_out) + ':' + str(minute_out) + ':00'
            rec.check_out_end_str = str(end_hour_out) + ':' + str(end_minute_out) + ':00'


class WorkingSchedule(models.Model):
    _inherit = 'resource.calendar'
    check_in_necessary = fields.Selection([('yes', 'Yes'), ('no', 'No')], default='yes',
                                          string='Necessary Check-In', required=True)
    check_out_necessary = fields.Selection([('yes', 'Yes'), ('no', 'No')], default='yes'
                                           , string='Necessary Check-Out', required=True)
    # check_in_early = fields.Selection([('yes', 'Yes'), ('no', 'No')], default='yes',
    #                                   string='Auto Overtime(Check-In Early)', required=True)
    # min_ot_check_in = fields.Integer(string='Min minutes OT(Check-In Early)', default=60, required=True)
    # check_out_delay = fields.Selection([('yes', 'Yes'), ('no', 'No')], default='yes',
    #                                    string='Auto Overtime(Check-Out Delay)', required=True)
    # min_ot_check_out = fields.Integer(string='Min minutes OT(Check-Out Delay)', default=60, required=True)
    break_start = fields.Float(string='Break Start Time', required=True)
    break_end = fields.Float(string='Break End Time', required=True)
    break_time = fields.Float(string='Break Time(m)')
    multiple_in_out = fields.Boolean(string='Multiple In & Out')
    aut_deduct = fields.Boolean(string='Auto Deduct')
    minimum_break_time = fields.Integer(string='Minimum Break Time')
    check_in_minute = fields.Integer(string='1 minute Late =', default=1)
    check_out_minute = fields.Integer(string='1 minute early =', default=1)
    # ot_working_day = fields.Float(string='1 minute working day overtime =', default=1.5)
    # ot_holiday = fields.Float(string='1 minute holiday overtime =', default=2)
    work_hours = fields.Float(string='Total Work Hours', default=8.0)
    month_work_days = fields.Integer(string='Total Work Days', default=30)
    check_in_late = fields.Integer(string='When Late exceeds', default=100, required=True)
    check_out_early = fields.Integer(string='when Early exceeds', default=100, required=True)
    no_check_in = fields.Selection([('late', 'Late'), ('absent', 'Absent'), ('not_complete', 'No Complete')],
                                   string='No Check In', help='When there is no Check-In, count as', default='late'
                                   , required=True)
    no_check_in_minute = fields.Integer(string='Minute', default=60)
    no_check_out = fields.Selection([('early', 'Early Leave'), ('absent', 'Absent'), ('not_complete', 'No Complete')],
                                    string='No Check Out', help='When there is no Check-Out, count as', default='early'
                                    , required=True)
    no_check_out_minute = fields.Integer(string='Minute', default=60)

    @api.constrains('attendance_ids' 'work_hours', 'month_work_days')
    def attendance_ids_cons(self):
        for rec in self:
            if rec.work_hours <= 0:
                raise UserError('Total Work Hours Must Be Greater Than 0.')
            if rec.month_work_days <= 0:
                raise UserError('Total Months Work Days Must Be Greater Than 0.')
            if not rec.attendance_ids:
                raise UserError('Please Enter  Working Time ')