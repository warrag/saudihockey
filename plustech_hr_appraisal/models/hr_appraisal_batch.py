# -*- coding: utf-8 -*-

import datetime
import logging

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.misc import format_date

_logger = logging.getLogger(__name__)


class HrAppraisalBatch(models.Model):
    _name = 'hr.appraisal.batch'

    def get_employee_ids(self):
        return  self.env['hr.employee'].search([])
    is_generate = fields.Boolean(copy=False)
    name = fields.Char("Name", copy=False, required=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company',  default=lambda self: self.env.company.id)
    department_id = fields.Many2one(comodel_name='hr.department', string='Department')
    appraisal_tmp_id = fields.Many2one('hr.appraisal.template', string='Appraisal Template')
    employee_ids = fields.Many2many(comodel_name='hr.employee', string='Employees', default=get_employee_ids )
    appraisal_ids = fields.One2many(comodel_name='hr.appraisal.appraisal',inverse_name='batch_id')
    appraisal_count = fields.Integer(compute="compute_appraisal_count")
    state = fields.Selection([
        ('new', 'Draft'),
        ('generated', 'Generated'),
    ],string='Status', tracking=True, required=True, copy=False, default='new')

    def get_appraisal_type(self):
        return self.env['ir.config_parameter'].sudo().get_param('plustech_hr_appraisal.appraisal_type')

    type = fields.Selection(string='Type', selection=[
        ('1', 'Monthly'),
        ('3', 'quarterly'),
        ('6', 'Semi'),
        ('12', 'Annually'),
    ], default=get_appraisal_type, required=True, )
    @api.depends('appraisal_ids')
    def compute_appraisal_count(self):
        for rec in self:
            rec.appraisal_count = len(rec.appraisal_ids.ids)

    @api.onchange('department_id')
    def change_department_id(self):
        for rec in self:
            if rec.department_id:
                employee_ids = self.env['hr.employee'].search([('department_id', '=', self.department_id.id)])
                rec.employee_ids = [(6, 0, employee_ids.ids)]

    def open_batch(self):
        view_id = self.env.ref('plustech_hr_appraisal.wizard_appraisal_batch_view_form')
        return {
            'name': 'Generate Appraisal Batch',
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': view_id.id,
            'res_model': 'hr.appraisal.batch',
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'target': 'new'
        }

    def generate_batch(self):
        for rec in self:
            for emp in rec.employee_ids:
                if not rec.appraisal_tmp_id and not emp.job_id.appraisal_tmp_id:
                    raise UserError(_('Employee ( %s ) has not appraisal template \n '
                                      'you can use batch appraisal template for all employees')%emp.name)
                appraisal_id =self.env['hr.appraisal.appraisal'].create({
                    'employee_id' : emp.id,
                    'batch_id' : rec.id,
                    'type' : rec.type,
                    'appraisal_tmp_id' : rec.appraisal_tmp_id.id if rec.appraisal_tmp_id else emp.job_id.appraisal_tmp_id.id,
                })
                appraisal_id.change_employee_get_assignment_date()
                appraisal_id.change_type()

            rec.is_generate = True
            rec.state = 'generated'

    def action_view_appraisals(self):
        action = self.env.ref("plustech_hr_appraisal.open_view_hr_appraisal_tree").sudo().read()[0]
        action["domain"] = [("id", "in", self.appraisal_ids.ids)]
        return action