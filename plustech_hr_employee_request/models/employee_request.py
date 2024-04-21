# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from datetime import date


_STATES = [
    ("draft", "Draft"),
    ("manager_approve", "Waiting For Manager Approval"),
    ('admin', 'Waiting For  Director of Financial and Administrative Affairs Approval'),
    ("rejected", "Rejected"),
    ("done", "Done"),
]


class EmployeeRequest(models.Model):

    _name = "hr.employee.request"
    _description = "HR Employee Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    @api.model
    def _company_get(self):
        return self.env["res.company"].browse(self.env.company.id)

    @api.model
    def _get_default_requested_by(self):
        return self.env["hr.employee"].search([('user_id', '=', self.env.uid)])

    @api.model
    def _get_default_name(self):
        return self.env["ir.sequence"].next_by_code("hr.employee.request")

    @api.depends("state")
    def _compute_is_editable(self):
        for rec in self:
            if rec.state in ("manager_approve", "admin", "rejected", "done"):
                rec.is_editable = False
            else:
                rec.is_editable = True

    name = fields.Char(
        string="Request Reference",
        required=True,
        default=lambda self: _("New"),
        tracking=True,
    )
    is_name_editable = fields.Boolean(
        default=lambda self: self.env.user.has_group("base.group_no_one"),
    )
    date = fields.Date(
        string="Request Date",
        help="Date when the user initiated the request.",
        default=fields.Date.context_today,
        tracking=True,
    )
    employee_id = fields.Many2one('hr.employee',  default=_get_default_requested_by,
                                  required=True,
                                  copy=False,
                                  tracking=True,
                                  index=True,
                                  )
    employee_number = fields.Char(related='employee_id.employee_number')
    job_id = fields.Many2one(related='employee_id.job_id', string='Job Position')
    department_id = fields.Many2one(related='employee_id.department_id', string='Department', store=True)
    manager_id = fields.Many2one(related='employee_id.parent_id', string='Manager')
    requested_by = fields.Many2one(
        comodel_name="res.users", store=True,
        copy=False, related='employee_id.user_id'
    )
    description = fields.Text()
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=False,
        default=_company_get,
        tracking=True,
    )
    line_ids = fields.One2many(
        comodel_name="hr.employee.request.line",
        inverse_name="request_id",
        string="Requested Product",
        readonly=False,
        copy=True,
        tracking=True,
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        related="line_ids.product_id",
        string="Product",
        readonly=True,
    )
    state = fields.Selection(
        selection=_STATES,
        string="Status",
        index=True,
        tracking=True,
        required=True,
        copy=False,
        default="draft",
    )
    is_editable = fields.Boolean(compute="_compute_is_editable", readonly=True)
    to_approve_allowed = fields.Boolean(compute="_compute_to_approve_allowed")
    line_count = fields.Integer(
        string="Employee Request Line count",
        compute="_compute_line_count",
        readonly=True,
    )
    currency_id = fields.Many2one(related="company_id.currency_id", readonly=True)
    estimated_cost = fields.Monetary(
        compute="_compute_estimated_cost",
        string="Total Estimated Cost",
        store=True,
    )
    approval_ids = fields.One2many('hr.employee.request.approvals', 'employee_request_id', string="Approver's")
    is_manager = fields.Boolean(compute='get_current_uid')


    @api.depends('manager_id')
    def get_current_uid(self):
        if self.manager_id.user_id.id == self.env.user.id:
            self.is_manager = True
        else:
            self.is_manager = False
            
    @api.depends("line_ids", "line_ids.estimated_cost")
    def _compute_estimated_cost(self):
        for rec in self:
            rec.estimated_cost = sum(rec.line_ids.mapped("estimated_cost"))

    @api.depends("line_ids")
    def _compute_line_count(self):
        for rec in self:
            rec.line_count = len(rec.mapped("line_ids"))

    def action_view_employee_request_line(self):
        action = (
            self.env.ref("plustech_hr_employee_request.hr_employee_request_line_form_action")
            .sudo()
            .read()[0]
        )
        lines = self.mapped("line_ids")
        if len(lines) > 1:
            action["domain"] = [("id", "in", lines.ids)]
        elif lines:
            action["views"] = [
                (self.env.ref("plustech_hr_employee_request.employee_request_line_form").id, "form")
            ]
            action["res_id"] = lines.ids[0]
        return action

    @api.depends("state", "line_ids.product_qty", "line_ids.cancelled")
    def _compute_to_approve_allowed(self):
        for rec in self:
            rec.to_approve_allowed = rec.state == "draft" and any(
                not line.cancelled and line.product_qty for line in rec.line_ids
            )

    def copy(self, default=None):
        default = dict(default or {})
        self.ensure_one()
        default.update({"state": "draft", "name": self._get_default_name()})
        return super(EmployeeRequest, self).copy(default)

    @api.model
    def _get_partner_id(self, request):
        user_id = self.env.user
        return user_id.partner_id.id

    @api.model
    def create(self, vals):
        if vals.get("name", _("New")) == _("New"):
            vals["name"] = self._get_default_name()
        request = super(EmployeeRequest, self).create(vals)

        return request

    def _can_be_deleted(self):
        self.ensure_one()
        return self.state == "draft"

    def unlink(self):
        for request in self:
            if not request._can_be_deleted():
                raise UserError(
                    _("You cannot delete a request which is not draft.")
                )
        return super(EmployeeRequest, self).unlink()

    def button_draft(self):
        self.mapped("line_ids").do_uncancel()
        return self.write({"state": "draft"})

    def button_submit(self):
        self.create_activity(self.id, self.manager_id.user_id)
        return self.write({"state": "manager_approve", 
                          'approval_ids': [(0, 0, {'user_id': self.env.user.id, 'name': self.state, 
                                          'state': 'approved', 'date': date.today()})]})

    def button_manager_approve(self):
        self._action_feedback_activity(self.env.user,self.env.ref('mail.mail_activity_data_todo'),self)
        self.create_activity(self.id, self.env['res.users'].search([]).filtered(lambda l: l.has_group('plustech_hr_employee_request.group_hr_employee_request_manager')))
        return self.write({"state": "admin", 
                          'approval_ids': [(0, 0, {'user_id': self.env.user.id, 'name': self.state, 
                                          'state': 'approved', 'date': date.today()})]})

    def button_admin_approve(self):
        self._action_feedback_activity(self.env.user,self.env.ref('mail.mail_activity_data_todo'),self)
        return self.write({"state": "done", 
                          'approval_ids': [(0, 0, {'user_id': self.env.user.id, 'name': self.state, 
                                          'state': 'approved', 'date': date.today()})]})

    def button_rejected(self):
        self.mapped("line_ids").do_cancel()
        return self.write({"state": "rejected", 
                          'approval_ids': [(0, 0, {'user_id': self.env.user.id, 'name': self.state, 
                                          'state': 'reject', 'date': date.today()})]})

    def check_auto_reject(self):
        """When all lines are cancelled the employee request should be
        auto-rejected."""
        for pr in self:
            if not pr.line_ids.filtered(lambda l: l.cancelled is False):
                pr.write({"state": "rejected"})



    def create_activity(self, record, users):
        print(users)
        for rec in users:
            self.env['mail.activity'].sudo().create({
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'res_id': record,
                'res_model_id': self.env['ir.model'].sudo().search([('model', '=', 'hr.employee.request')], limit=1).id,
                'icon': 'fa-pencil-square-o',
                'date_deadline': fields.Date.today(),
                'user_id': rec.id,
                'summary': _("Waiting your approval"),
                'note': _("This request is waiting your approval")
            })

    
    def _action_feedback_activity(self, user, activity_type, record):
        self.sudo()._get_user_approval_activities(
                                                    activity_type=activity_type,
                                                    record=record).action_feedback()

    def _get_user_approval_activities(self, activity_type, record):
        domain = [
            ('res_model', '=', 'hr.employee.request'),
            ('res_id', 'in', record.ids),
            ('activity_type_id', '=', activity_type.id),
        ]
        activities = self.env['mail.activity'].search(domain)
        return activities