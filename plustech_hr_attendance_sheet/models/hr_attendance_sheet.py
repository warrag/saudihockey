# -*- coding:utf-8 -*-

from odoo import api, fields, models, _
from datetime import date
import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools.misc import format_date


class HrAttendanceSheet(models.Model):
    _name = 'hr.attendance.sheet'
    _description = 'HR Attendance Sheet'

    name = fields.Char(struct='Name', compute='_compute_name', store=True, )
    date_from = fields.Date(string='Date From', default=lambda self: fields.Date.to_string(date.today().replace(day=1)),
                            reqiured=True)
    date_to = fields.Date(string='Date To', default=lambda self: fields.Date.to_string((datetime.datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()),
                          required=True)
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirmed'),
                              ('approve', 'Approve'), ('cancel', 'Cancel')], default='draft', string='State')

    line_ids = fields.One2many('hr.attendance.sheet.line', 'sheet_id', string='Lines')
    deducted = fields.Boolean(string='Deducted')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    @api.depends('date_from')
    def _compute_name(self):
        for sheet in self.filtered(lambda p: p.date_from):
            lang = self.env.user.lang
            context = {'lang': lang}
            sheet_name = _('Attendance Sheet')
            del context
            sheet.name = '%(sheet_name)s - %(dates)s' % {
                'sheet_name': sheet_name,
                'dates': format_date(self.env, sheet.date_from, date_format="MMMM y", lang_code=lang)
            }

    def compute_attendance(self):
        self.line_ids = None
        employees = self.env['hr.employee'].search([('contract_id', '!=', False), ('contract_id.state', '=', 'open')])
        lines = []
        for emp in employees:

            attendance_transactions = self.env['attendance.transaction'].search([('employee_id', '=', emp.id),
                                                                                ('date', '>=', self.date_from),
                                                                                ('date', '<=', self.date_to),
                                                                                ('status', 'in', ['ex', 'ab'])])
            planned_hours = sum(attendance_transactions.mapped('pl_hours'))
            act_hours = sum([line.ac_sign_out - line.ac_sign_in for line in attendance_transactions]) or 0.0
            late_in = sum(attendance_transactions.mapped('late_in')) or 0.0
            early_exit = sum(attendance_transactions.mapped('early_exit')) or 0.0
            diff_time = sum(attendance_transactions.mapped('diff_time')) or 0.0
            overtime = sum(attendance_transactions.mapped('overtime')) or 0.0
            deduction_amount = sum(attendance_transactions.mapped('deducted_amount'))
            last_ded_id = self.env['hr.attendance.sheet.line'].search([
                ('employee_id', '=', emp.id),
                ('sheet_id.date_from', '<', self.date_from),
                ('sheet_id.state', '!=', 'draft'),
            ], order='date_from DESC', limit=1)
            last_ded_amount = last_ded_id.will_postpone_ded if last_ded_id else 0
            absence_days = len(attendance_transactions.filtered(lambda line: line.status == 'ab'))
            new_line = {
                'employee_id': emp.id,
                'planned_hours': planned_hours,
                'act_hours': act_hours,
                'late_in': late_in,
                'early_exit': early_exit,
                'diff_time': diff_time,
                'absence_days': absence_days,
                'deduction_amount': deduction_amount,
                'overtime': overtime,
                'last_ded_amount': last_ded_amount,
                'will_postpone_ded': 0,
            }
            lines.append((0, 0, new_line))

        self.write({'line_ids': lines})

    def action_confirm(self):
        self.state = 'confirm'

    def action_approve(self):
        self.state = 'approve'

    def action_cancel(self):
        self.state = 'cancel'


class HrAttendanceLines(models.Model):
    _name = 'hr.attendance.sheet.line'

    sheet_id = fields.Many2one('hr.attendance.sheet', ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', readonly=1)
    planned_hours = fields.Float(string='PL-Hours', readonly=1)
    act_hours = fields.Float(string='ACT-Hours', readonly=1)
    absence_days = fields.Integer(string='Absence Days', readonly=1)
    late_in = fields.Float(string='Late In', readonly=1)
    early_exit = fields.Float(string='Early Exit', readonly=1)
    diff_time = fields.Float(string='Diff Time', readonly=1)
    overtime = fields.Float(string='OverTime', readonly=1)
    deduction_amount = fields.Float(string='Deduction Amount')
    last_ded_amount = fields.Float(string='Last Deduction')
    total_ded_amount = fields.Float(string='Total Deduction', compute='_compute_deduction_amount')
    # postpone_amount = fields.Float(string='Postpone Amount')
    will_postpone_ded = fields.Float(string='Will Postpone')
    date_from = fields.Date(string='Date From', related="sheet_id.date_from", store="1")
    state = fields.Selection(string='state', related="sheet_id.state", store="1")

    def open_attendance(self):
        self.ensure_one()
        action = self.env.ref("plustech_hr_attendance_transaction.action_attendance_transaction").read()[0]
        attendance = self.env['attendance.transaction'].search([('employee_id', '=', self.employee_id.id)])
        attendance_ids = attendance.filtered(
            lambda a: self.sheet_id.date_from <= a.date <= self.sheet_id.date_to)
        action["domain"] = [("id", "in", attendance_ids.ids)]
        action["target"] = 'new'
        action['context'] = {'search_default_today': 0}
        return action



    @api.depends('absence_days', 'last_ded_amount')
    def _compute_deduction_amount(self):
        for line in self:
            line.total_ded_amount = line.deduction_amount + line.last_ded_amount - line.will_postpone_ded

    def open_postpone_deduction(self):
        view = self.env.ref('plustech_hr_attendance_transaction.postpone_view_form')
        return {
            'name': ('POSTPONE'),
            'help': "POSTPONE TIP",
            'view_mode': 'form',
            'view_id': view.id,
            'res_model': 'hr.attendance.sheet.line',
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'target': 'new'
        }

    def action_postpone(self):
        self.total_ded_amount = self.deduction_amount + self.last_ded_amount - self.will_postpone_ded
