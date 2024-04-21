# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_STATES = [
    ("draft", "Draft"),
    ("manager_approve", "Waiting For Manager Approval"),
    ('admin', 'Waiting For  Director of Financial and Administrative Affairs Approval'),
    ("rejected", "Rejected"),
    ("done", "Done"),
]


class EmployeeRequestLine(models.Model):

    _name = "hr.employee.request.line"
    _description = "HR Employee Request Line"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    name = fields.Char(string="Description", tracking=True)
    product_uom_id = fields.Many2one(
        comodel_name="uom.uom",
        string="UoM",
        tracking=True,
        domain="[('category_id', '=', product_uom_category_id)]",
    )
    product_uom_category_id = fields.Many2one(related="product_id.uom_id.category_id")
    product_qty = fields.Float(
        string="Quantity", tracking=True, digits="Product Unit of Measure"
    )
    request_id = fields.Many2one(
        comodel_name="hr.employee.request",
        string="Employee Request",
        ondelete="cascade",
        readonly=True,
        index=True,
        auto_join=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        related="request_id.company_id",
        string="Company",
        store=True,
    )
    analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="Analytic Account",
        tracking=True,
    )
    analytic_tag_ids = fields.Many2many(
        "account.analytic.tag", string="Analytic Tags", tracking=True
    )
    requested_by = fields.Many2one(
        comodel_name="res.users",
        related="request_id.requested_by",
        string="Requested by",
        store=True,
    )
    date = fields.Date(related="request_id.date", store=True)
    description = fields.Text(
        related="request_id.description",
        string="PR Description",
        store=True,
        readonly=False,
    )
    date_required = fields.Date(
        string="Request Date",
        required=True,
        tracking=True,
        default=fields.Date.context_today,
    )
    is_editable = fields.Boolean(compute="_compute_is_editable", readonly=True)
    specifications = fields.Text()
    request_state = fields.Selection(
        string="Request state",
        related="request_id.state",
        store=True,
    )

    cancelled = fields.Boolean(readonly=True, default=False, copy=False)
    estimated_cost = fields.Monetary(
        currency_field="currency_id",
        default=0.0,
        help="Estimated cost of Purchase Request Line, not propagated to PO.",
    )
    currency_id = fields.Many2one(related="company_id.currency_id", readonly=True)
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product",
        domain=[("purchase_ok", "=", True)],
        tracking=True,
    )

    @api.depends(
        "product_id",
        "name",
        "product_uom_id",
        "product_qty",
        "analytic_account_id",
        "date_required",
        "specifications",
    )
    def _compute_is_editable(self):
        for rec in self:
            if rec.request_id.state in ("to_approve", "approved", "rejected", "done"):
                rec.is_editable = False
            else:
                rec.is_editable = True

    @api.onchange("product_id")
    def onchange_product_id(self):
        if self.product_id:
            name = self.product_id.name
            if self.product_id.code:
                name = "[{}] {}".format(self.product_id.code, name)
            if self.product_id.description_purchase:
                name += "\n" + self.product_id.description_purchase
            self.product_uom_id = self.product_id.uom_id.id
            self.product_qty = 1
            self.name = name

    def do_cancel(self):
        """Actions to perform when cancelling a purchase request line."""
        self.write({"cancelled": True})

    def do_uncancel(self):
        """Actions to perform when uncancelling a purchase request line."""
        self.write({"cancelled": False})

    def write(self, vals):
        res = super(EmployeeRequestLine, self).write(vals)
        if vals.get("cancelled"):
            requests = self.mapped("request_id")
            requests.check_auto_reject()
        return res

    def _can_be_deleted(self):
        self.ensure_one()
        return self.request_state == "draft"

    def unlink(self):
        for line in self:
            if not line._can_be_deleted():
                raise UserError(
                    _(
                        "You can only delete a request line "
                        "if the request is in draft state."
                    )
                )
        return super(EmployeeRequestLine, self).unlink()

    def action_show_details(self):
        self.ensure_one()
        view = self.env.ref("plustech_hr_employee_request.view_employee_request_line_details")
        return {
            "name": _("Detailed Line"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "hr.employee.request.line",
            "views": [(view.id, "form")],
            "view_id": view.id,
            "target": "new",
            "res_id": self.id,
            "context": dict(
                self.env.context,
            ),
        }
