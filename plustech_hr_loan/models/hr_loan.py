# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from lxml import etree


class HrLoan(models.Model):
    _name = 'hr.loan'
    _inherit = ['mail.thread']
    _description = "Loan Request"
    _order = 'id desc'

    def _compute_loan_amount(self):
        total_paid = 0.0
        for loan in self:
            for line in loan.loan_lines:
                if line.paid:
                    total_paid += line.amount
            balance_amount = loan.loan_amount - total_paid
            self.total_amount = loan.loan_amount
            self.balance_amount = balance_amount
            self.total_paid_amount = total_paid

    @api.model
    def get_default_employee(self):
        employee_obj = self.env['hr.employee']
        emp_id = False
        if not self.env.user.has_group('hr.group_hr_user') and not self.env.user.has_group('hr.group_hr_manager'):
            emp_id = employee_obj.search([('user_id.id', '=', self.env.user.id)])

        return emp_id and emp_id[0].id or False

    name = fields.Char(string="Loan Name", default="/", readonly=True)
    date = fields.Date(string="Loan received date", default=fields.Date.today())
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, default=get_default_employee)
    department_id = fields.Many2one('hr.department', related='employee_id.department_id')
    job_id = fields.Many2one('hr.job', related='employee_id.job_id')
    employee_number = fields.Char(related='employee_id.employee_number')
    installment_type = fields.Selection([('end_date', 'With Installments End Date'),
                                         ('amount', 'With Installments Amount')], required=True,
                                        string="Type Of Installments", default='amount')
    installment = fields.Float(string="monthly installment")
    payment_date = fields.Date(string="Payment Start Date")
    payment_end_date = fields.Date(string="Payment End Date")
    loan_lines = fields.One2many('hr.loan.line', 'loan_id', string="Loan Line", index=True, copy=True, auto_join=True)
    loan_account_id = fields.Many2one('account.account', string="Loan Account")
    treasury_account_id = fields.Many2one('account.account', string="Treasury Account")
    loan_journal_id = fields.Many2one('account.journal', string="Journal")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)
    loan_amount = fields.Float(string="Loan Amount", required=True)
    total_amount = fields.Float(string="Total Amount", readonly=True, compute='_compute_loan_amount')
    balance_amount = fields.Float(string="Balance Amount", compute='_compute_loan_amount')
    total_paid_amount = fields.Float(string="Total Paid Amount", compute='_compute_loan_amount')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approval_1', 'Submitted'),
        ('waiting_approval_2', 'Waiting Approval'),
        ('acceptance', 'Waiting Employee Acceptance'),
        ('approve', 'Approved'),
        ('refuse', 'Refused'),
        ('cancel', 'Canceled'),
    ], string="State", default='draft', tracking=True, copy=False, )
    analytic_account_id = fields.Many2one(
        'account.analytic.account', string="Analytic Account")
    payment_status = fields.Selection([('not_paid', 'Not Paid'), ('paid', 'Paid')],
                                      default='not_paid', compute='compute_payment_status')
    loan_type_id = fields.Many2one('loan.type', string='Loan Type', check_company=True)
    actual_salary = fields.Float(string='Actual Salary')
    previous_amount = fields.Float(string='Previous Amount', compute='_compute_previous_loan_amount')
    note = fields.Html(string='Notes')
    guarantor_id = fields.Many2one('hr.employee', string='Guarantor')
    employee_acknowledgment = fields.Text(related="loan_type_id.acknowledgment", string='Employee Acknowledgment',
                                          readonly=False, required=True)
    is_employee = fields.Boolean(compute='request_owner')
    current_user_id = fields.Many2one('res.users', compute='get_current_user')

    @api.depends('current_user_id')
    def request_owner(self):
        for record in self:
            if record.current_user_id == record.employee_id.user_id:
                record.is_employee = True
            else:
                record.is_employee = False

    def get_current_user(self):
        for record in self:
            record.current_user_id = self.env.user

    @api.onchange('employee_id', 'job_id')
    def get_loan_type(self):
        domain = [('loan_policy_id.job_position_ids', 'in', self.job_id.ids)]
        return {'domain': {'loan_type_id': domain}}

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        self.actual_salary = self.employee_id.contract_id.monthly_yearly_costs

    @api.depends('employee_id', 'date')
    def _compute_previous_loan_amount(self):
        for record in self:
            previous_loans = self.search([('employee_id', '=', record.employee_id.id), ('state', '=', 'approve'),
                                          ('date', '<=', self.date), ('id', '!=', self._origin.id)])
            record.previous_amount = sum(previous_loans.mapped('loan_amount'))

    @api.depends('loan_lines.state', 'state')
    def compute_payment_status(self):
        for record in self:
            loan_ids = record.loan_lines.filtered(lambda line: not line.paid)
            if loan_ids or self.state == 'draft':
                record.payment_status = 'not_paid'
            else:
                record.payment_status = 'paid'

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        employee_obj = self.env['hr.employee']
        if not self.env.user.has_group('hr.group_hr_user') and not self.env.user.has_group('hr.group_hr_manager'):
            emp_id = employee_obj.search([('user_id.id', '=', self.env.user.id)])
            args += [('employee_id', 'in', [emp_id.id])]
        return super(HrLoan, self).search(args=args, offset=offset, limit=limit, order=order, count=count)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(HrLoan, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
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

    @api.constrains('payment_date', 'payment_end_date', 'date')
    def _check_date(self):
        for record in self:
            if record.installment_type == 'end_date':
                if record.payment_end_date < record.payment_date:
                    raise ValidationError(_('"Payment End Date" cannot be earlier than "Payment Start Date".'))
            loan = self.env['hr.loan'].search([('employee_id', '=', self.employee_id.id), ('state', '=', 'approve')])
            if loan:
                loan_date = loan.mapped('date')
                latest = max(loan_date)
                period = relativedelta(self.date, latest)
                min_years = self.loan_type_id.loan_policy_id.min_years
                if period.years < min_years:
                    raise ValidationError(_("Minimum years allowed to get another loan is %s") % min_years)

    @api.constrains('loan_amount')
    def _check_amount(self):
        for record in self:
            policy = record.loan_type_id.loan_policy_id
            if sum(line.amount for line in record.loan_lines) > record.loan_amount:
                raise ValidationError(_('The installments amount can\'t be grate than Loan amount.'))
            if 0 < policy.max_amount < record.loan_amount:
                raise ValidationError(_('The maximum amount allowed is %s!') % policy.max_amount)
            salary = self.employee_id.contract_id.wage if policy.salary_type == 'basic' else record.actual_salary
            if policy.max_salaries > 0 and record.loan_amount > (policy.max_salaries * salary):
                raise ValidationError(_('The maximum salaries allowed is %s!') % policy.max_salaries)

    @api.constrains('loan_amount', 'installment', 'payment_end_date', 'payment_date')
    def _check_installments_period(self):
        if self.installment < 1 and self.installment_type == 'amount':
            raise UserError(_("Installment amount must be grater than zero!"))
        payment_period = max_month_allowed = self.loan_type_id.loan_policy_id.max_payment_period
        if self.installment_type == 'end_date' and self.payment_date and self.payment_end_date:
            payment_period = relativedelta(self.payment_end_date, self.payment_date).months + 1
        elif self.installment_type == 'amount':
            payment_period = self.loan_amount / self.installment
        if payment_period > max_month_allowed:
            raise ValidationError(_('Maximum payment period allowed is %s months'
                                    '\n Your payment period is %s months!') % (max_month_allowed, payment_period))

    @api.model
    def create(self, values):
        policy = self.env['loan.type'].browse(values['loan_type_id']).loan_policy_id
        if not policy.allow_multi:
            loan_count = self.env['hr.loan'].search_count(
                [('employee_id', '=', values['employee_id']), ('state', '=', 'approve'),
                 ('balance_amount', '!=', 0)])
            if loan_count:
                raise ValidationError(_("The employee has already a pending installment"))
        seq_date = None
        if 'date' in values:
            seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(values['date']))
        values['name'] = self.env['ir.sequence'].next_by_code('hr.loan.seq', sequence_date=seq_date) or '/'
        res = super(HrLoan, self).create(values)
        print(res)
        return res

    def unlink(self):
        if any(self.filtered(lambda loan: loan.state not in ['draft'])):
            raise UserError(_('You cannot delete a loan request which is not draft!'))
        return super(HrLoan, self).unlink()

    def action_acceptance(self):
        self.write({'state': 'waiting_approval_2'})

    def action_refuse(self):
        return self.write({'state': 'refuse'})

    def action_submit(self):
        if len(self.loan_lines) == 0:
            raise ValidationError(_("Please generate installments before submit"))
        self.write({'state': 'waiting_approval_1'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_approve(self):
        self.write({'state': 'approve'})

    def compute_installment(self):
        """
        This automatically create the installment the employee need to pay to
        company based on payment start date and the no of installments.
        """
        loan_line = self.env['hr.loan.line']
        for loan in self:
            if loan.loan_lines:
                if any(loan.paid for loan in loan.loan_lines):
                    raise ValidationError(_('Error! This loan have alrady paid installments!'))
                loan.loan_lines.unlink()
            date_start = datetime.strptime(str(loan.payment_date), '%Y-%m-%d')
            if loan.installment_type == 'amount':
                amount = loan.loan_amount
                emi_count = 1
                while amount > loan.installment:
                    name = 'EMI - ' + self.name + ' - ' + str(emi_count)
                    amount -= loan.installment
                    loan_line.create({
                        'name': name,
                        'date': date_start,
                        'amount': loan.installment,
                        'employee_id': loan.employee_id.id,
                        'loan_id': loan.id})
                    date_start = date_start + relativedelta(months=1)
                    emi_count += 1
                name = 'EMI - ' + self.name + ' - ' + str(emi_count)
                if amount <= loan.installment:
                    loan_line.create({
                        'name': name,
                        'date': date_start,
                        'amount': amount,
                        'employee_id': loan.employee_id.id,
                        'loan_id': loan.id})
                loan.payment_end_date = date_start
            else:
                date_end = datetime.strptime(str(loan.payment_end_date), '%Y-%m-%d')
                date_end_temp = date_end
                months = (date_end.year - date_start.year) * 12 + date_end.month - date_start.month
                installment = loan.loan_amount / (months + 1)
                emi_count = months + 1
                for month in range(1, months + 2):
                    name = 'EMI - ' + self.name + ' - ' + str(emi_count)
                    if date_end_temp.month == date_start.month and date_end_temp.year == date_start.year:
                        loan_line.create({
                            'name': name,
                            'date': date_start,
                            'amount': installment,
                            'employee_id': loan.employee_id.id,
                            'loan_id': loan.id})
                        break
                    loan_line.create({
                        'name': name,
                        'date': date_end_temp,
                        'amount': installment,
                        'employee_id': loan.employee_id.id,
                        'loan_id': loan.id})
                    date_end_temp = date_end + relativedelta(months=-month)
                    emi_count -= 1
        return True

    def recompute_installment(self, diff, change_line, loan):
        residual = 0.0
        count = 0
        for line in loan.loan_lines:
            if not line.paid and line != change_line:
                residual += line.amount
                count += 1
        lines_amount = residual + diff
        amount = lines_amount / count
        for line in loan.loan_lines:
            if not line.paid and line.id != change_line.id:
                line.amount = amount
        return True

    def button_open_journal_entry(self):
        """ Redirect the user to this loan journal.
        :return:    An action on account.move.
        """
        self.ensure_one()
        return {
            'name': _("Journal Items"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move.line',
            'context': {'create': False},
            'view_mode': 'form',
            'views': [(False, 'tree'), (False, 'form')],
            # 'res_id': self.move_id.id,
            'domain': [('display_type', 'not in', ('line_section', 'line_note')), ('loan_id', '=', self.id)],
            'context': {'journal_type': 'general', 'search_default_group_by_move': 1, 'search_default_posted': 1,
                        'name_groupby': 1, 'create': 0}
        }


class InstallmentLine(models.Model):
    _name = "hr.loan.line"
    _description = "Installment Line"
    _order = "date asc"

    name = fields.Char('Name')
    date = fields.Date(string="Payment Date", required=True)
    employee_id = fields.Many2one('hr.employee', string="Employee")
    amount = fields.Float(string="Amount", required=True)
    paid = fields.Boolean(string="Paid")
    loan_id = fields.Many2one('hr.loan', string="Loan Ref.", required=True, ondelete='cascade', index=True, copy=False)
    payslip_id = fields.Many2one('hr.payslip', string="Payslip Ref.")
    state = fields.Selection([('draft', 'Draft'), ('pending', 'Pending'),
                              ('paid', 'Paid'), ('cancel', 'Cancelled')], default='draft')
    loan_journal_id = fields.Many2one(related='loan_id.loan_journal_id', store=True, string="Journal")

    def write(self, vals):
        for line in self:
            line_amount = line.amount
            res = super(InstallmentLine, self).write(vals)
            if 'amount' in vals:
                if line.payslip_id and (line.paid or ('paid' in vals and vals['paid'])):
                    diff = line_amount - vals['amount']
                    line.loan_id.recompute_installment(diff, line, line.loan_id)
                elif line.payslip_id and not (line.paid or ('paid' in vals and vals['paid'])):
                    raise ValidationError(_('You can\'t update non paid installment that associated with payslip.'))
        return res


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _compute_employee_loans(self):
        """This compute the loan amount and total loans count of an employee.
            """
        self.loan_count = self.env['hr.loan'].search_count([('employee_id', '=', self.id)])

    loan_count = fields.Integer(string="Loan Count", compute='_compute_employee_loans')
