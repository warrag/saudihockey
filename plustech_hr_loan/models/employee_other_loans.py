# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from lxml import etree
from odoo.exceptions import ValidationError


class EmployeeOtherLoans(models.Model):
    _name = 'employee.other.loan'
    _inherit = ['mail.thread']
    _description = "Other Loan Request"

    @api.model
    def get_default_employee(self):
        employee_obj = self.env['hr.employee']
        emp_id = False
        if not self.env.user.has_group('hr.group_hr_user') and not self.env.user.has_group('hr.group_hr_manager'):
            emp_id = employee_obj.search([('user_id.id', '=', self.env.user.id)])

        return emp_id and emp_id[0].id or False

    name = fields.Char(string="Loan Name", default="/", readonly=True)
    date = fields.Date(string="date", default=fields.Date.today(), required=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, default=get_default_employee)
    department_id = fields.Many2one('hr.department', related='employee_id.department_id', string='Department')
    job_id = fields.Many2one('hr.job', related='employee_id.job_id', string='Job Position')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)
    loaner_id = fields.Many2one('res.partner', string='Loaner')
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Runnig'),
        ('close', 'closed'),
        ('cancel', 'Canceled'),
    ], string="State", default='draft', tracking=True, copy=False, )

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        employee_obj = self.env['hr.employee']
        if not self.env.user.has_group('hr.group_hr_user') and not self.env.user.has_group('hr.group_hr_manager'):
            emp_id = employee_obj.search([('user_id.id', '=', self.env.user.id)])
            args += [('employee_id', 'in', [emp_id.id])]
        return super(EmployeeOtherLoans, self).search(args=args, offset=offset, limit=limit, order=order, count=count)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(EmployeeOtherLoans, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                              submenu=submenu)
        employee_obj = self.env['hr.employee']
        if view_type == 'form':
            if not self.env.user.has_group('hr.group_hr_user') and not self.env.user.has_group('hr.group_hr_manager'):
                emp_id = employee_obj.search([('user_id.id', '=', self.env.user.id)])
                if emp_id:
                    doc = etree.XML(res['arch'])
                    for node in doc.xpath("//field[@name='employee_id']"):
                        domain = [('id', '=', emp_id[0].id)]
                        node.set('domain', str(domain))
                    res['arch'] = etree.tostring(doc)
                else:
                    doc = etree.XML(res['arch'])
                    for node in doc.xpath("//field[@name='employee_id']"):
                        domain = [('id', '=', -1)]
                        node.set('domain', str(domain))
                    res['arch'] = etree.tostring(doc)
        return res

    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].get('other.loan.seq') or '/'
        res = super(EmployeeOtherLoans, self).create(values)
        return res

    def action_confirm(self):
        self.write({'state': 'confirm'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_close(self):
        self.write({'state': 'close'})

    def unlink(self):
        for record in self:
            if not record.first_stage:
                raise ValidationError(_("You can't delete record not in draft state"))
        res = super(EmployeeOtherLoans, self).unlink()
        return res


