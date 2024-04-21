from odoo import models, fields, api, _
from odoo.tools import float_is_zero
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
from odoo.addons.hr_payroll_account.models.hr_payroll_account import HrPayslip as OriginalHrPayslip


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    payslip_period = fields.Integer(
        string='Payslip Days', compute="compute_period")
    out_days = fields.Integer(
        compute='_get_out_of_period_days', string='Out Of Period Day(s)', tracking=True)
    paid_days = fields.Integer(
        compute='_get_out_of_period_days', string='In Period Day(s)')
    adjust_days = fields.Integer(readonly=1)
    payslip_type = fields.Selection(
        [('normal', 'Normal')], string='Payslip Type', default='normal')
    gosi_company_daily = fields.Float(string='Daily Company Deduction')
    gosi_employee_daily = fields.Float(string='Daily Employee Deduction')

    def compute_sheet(self):
        for slip in self:
            gosi_employee_daily = 0.0
            gosi_company_daily = 0.0
            if slip.employee_id.join_date.month == slip.date_from.month and slip.employee_id.join_date.year == slip.date_from.year and slip.date_from.day != 1:
                gosi_id = self.env['gosi.daily.contribution'].search([('sequence', '=', slip.date_from.month),('contract_id', '=', slip.contract_id.id)],limit=1)
                gosi_employee_daily = gosi_id.gosi_employee_daily
                gosi_company_daily = gosi_id.gosi_company_daily
            else:
                gosi_employee_daily = slip.contract_id.gosi_employee_daily
                gosi_company_daily = slip.contract_id.gosi_company_daily

            slip.gosi_company_daily = gosi_company_daily * slip.paid_days
            slip.gosi_employee_daily = gosi_employee_daily * slip.paid_days
            
        result = super(HrPayslip, self).compute_sheet()
        return result

    @api.depends('date_from', 'date_to', 'employee_id')
    def _get_out_of_period_days(self):
        for slip in self:
            contract = slip.contract_id
            out_days = 0
            if slip.contract_id and slip.date_from < contract.date_start:
                start = fields.Datetime.to_datetime(slip.date_from)
                stop = fields.Datetime.to_datetime(
                    contract.date_start) + relativedelta(days=-1, hour=23, minute=59)
                period = stop - start
                out_days += period.days
            if contract.date_end and contract.date_end < slip.date_to:
                start = fields.Datetime.to_datetime(
                    contract.date_end) + relativedelta(days=1)
                stop = fields.Datetime.to_datetime(
                    slip.date_to) + relativedelta(hour=23, minute=59)
                period = stop - start
                out_days += period.days
            slip.out_days = out_days
            slip.paid_days = (
                (slip.date_to - slip.date_from).days + 1) - out_days
            if slip.date_from.day == slip.date_to.day:
                if slip.date_from.month == 2:
                    slip.paid_days = (
                        slip.date_to - slip.date_from).days + 2 - out_days
                    slip.adjust_days = 1
                else:
                    slip.paid_days = (
                        slip.date_to - slip.date_from).days - out_days - 1
                    slip.adjust_days = 2 if slip.date_to.month == 2 else -2
            if slip.date_to.day == 31:
                slip.paid_days = (
                    slip.date_to - slip.date_from).days - out_days
                slip.adjust_days = -1
            if slip.date_from.month == 2 and slip.date_from.day == 1 and out_days == 0:
                if slip.paid_days == 29:
                    slip.paid_days = slip.paid_days + 1
                    slip.adjust_days = 1
                elif slip.paid_days == 28:
                    slip.paid_days = slip.paid_days + 2
                    slip.adjust_days = 2

    @api.depends('contract_id')
    def _compute_struct_id(self):
        for slip in self.filtered(lambda p: not p.struct_id):
            slip.struct_id = slip.contract_id.struct_id or slip.contract_id.structure_type_id.default_struct_id

    @api.model
    def create(self, vals):
        contract_id = self.env['hr.contract'].browse(int(vals['contract_id']))
        vals['struct_id'] = contract_id.struct_id.id or contract_id.structure_type_id.default_struct_id.id
        res = super(HrPayslip, self).create(vals)
        return res

    @api.depends('date_from', 'date_to')
    def compute_period(self):
        for record in self:
            record.payslip_period = (record.date_to - record.date_from).days

    def _prepare_line_values(self, line, account_id, date, debit, credit):
        result = super(HrPayslip, self)._prepare_line_values(
            line, account_id, date, debit, credit)
        for rec in self:
            if line.slip_id.id == rec.id and rec.company_id.payslip_entry_generation == 'separate':
                result['partner_id'] = rec.employee_id.address_home_id.id
        return result

    def _prepare_slip_lines(self, date, line_ids):
        self.ensure_one()
        precision = self.env['decimal.precision'].precision_get('Payroll')
        new_lines = []
        for line in self.line_ids.filtered(lambda line: line.category_id):
            amount = -line.total if self.credit_note else line.total
            if line.code == 'NET':  # Check if the line is the 'Net Salary'.
                for tmp_line in self.line_ids.filtered(lambda line: line.category_id):
                    # Check if the rule must be computed in the 'Net Salary' or not.
                    if tmp_line.salary_rule_id.not_computed_in_net:
                        if amount > 0:
                            amount -= abs(tmp_line.total)
                        elif amount < 0:
                            amount += abs(tmp_line.total)
            if float_is_zero(amount, precision_digits=precision):
                continue
            debit_account_id = line.salary_rule_id.account_debit.id
            credit_account_id = line.salary_rule_id.account_credit.id

            if debit_account_id:  # If the rule has a debit account.
                debit = amount if amount > 0.0 else 0.0
                credit = -amount if amount < 0.0 else 0.0

                debit_line = self._get_existing_lines(
                    line_ids + new_lines, line, debit_account_id, debit, credit)

                if not debit_line or debit_line['partner_id']:
                    debit_line = self._prepare_line_values(
                        line, debit_account_id, date, debit, credit)
                    debit_line['tax_ids'] = [
                        (4, tax_id) for tax_id in line.salary_rule_id.account_debit.tax_ids.ids]
                    new_lines.append(debit_line)
                else:
                    debit_line['debit'] += debit
                    debit_line['credit'] += credit

            if credit_account_id:  # If the rule has a credit account.
                debit = -amount if amount < 0.0 else 0.0
                credit = amount if amount > 0.0 else 0.0
                credit_line = self._get_existing_lines(
                    line_ids + new_lines, line, credit_account_id, debit, credit)

                if not credit_line or credit_line['partner_id']:
                    credit_line = self._prepare_line_values(
                        line, credit_account_id, date, debit, credit)
                    credit_line['tax_ids'] = [
                        (4, tax_id) for tax_id in line.salary_rule_id.account_credit.tax_ids.ids]
                    new_lines.append(credit_line)
                else:
                    credit_line['debit'] += debit
                    credit_line['credit'] += credit
        return new_lines

    OriginalHrPayslip._prepare_slip_lines = _prepare_slip_lines

    def _prepare_adjust_line(self, line_ids, adjust_type, debit_sum, credit_sum, date):
        acc_id = self.sudo().struct_id.default_account_id.id
        if not acc_id:
            raise UserError(_('The Expense Structure "%s" has not properly configured the default Account!') % (
                self.struct_id.name))
        existing_adjustment_line = (
            line_id for line_id in line_ids if line_id['name'] == _('Adjustment Entry')
        )
        adjust_credit = next(existing_adjustment_line, False)

        if not adjust_credit:
            adjust_credit = {
                'name': _('Adjustment Entry'),
                'partner_id': False,
                'account_id': acc_id,
                'journal_id': self.journal_id.id,
                'date': date,
                'debit': 0.0 if adjust_type == 'credit' else credit_sum - debit_sum,
                'credit': debit_sum - credit_sum if adjust_type == 'credit' else 0.0,
            }
            line_ids.append(adjust_credit)
        else:
            adjust_credit['credit'] = debit_sum - credit_sum

    OriginalHrPayslip._prepare_adjust_line = _prepare_adjust_line

    def _get_worked_day_lines(self, domain=None, check_out_of_contract=True):
        res = super(HrPayslip, self)._get_worked_day_lines(
            domain, check_out_of_contract)
        self._get_out_of_period_days()
        if self.adjust_days != 0:
            work_entry_type = self.env.ref(
                'plustech_hr_payroll.hr_work_entry_type_working_days_adjust')
            amount = (self.contract_id.contract_wage / 30) * self.adjust_days
            res.append({
                'sequence': work_entry_type.sequence,
                'work_entry_type_id': work_entry_type.id,
                'number_of_days': self.adjust_days,
                'number_of_hours': self.adjust_days*8,
                'amount': amount,
            })
        return res

    def _get_worked_day_lines_values(self, domain=None):
        res = super(HrPayslip, self)._get_worked_day_lines_values(domain)
        for entry in res:
            work_entries = self.env['hr.work.entry'].search([('employee_id', '=', self.employee_id.id),
                                                             ('state', '=', 'draft')])
            work_entries = work_entries.filtered(lambda line: line.work_entry_type_id.id == entry['work_entry_type_id'] and line.date_start.date(
            ) >= self.date_from and line.date_stop.date() <= self.date_to)
            entry['number_of_days'] = len(work_entries)
        return res


class HrPayslipWorkedDays(models.Model):
    _inherit = 'hr.payslip.worked_days'

    is_leave_advance = fields.Boolean(string='Leave Advance')
    days = fields.Char(string='Days', readonly=1)
    hours = fields.Char(string='Hours', readonly=1)

    import_from_attendance = fields.Boolean(
        string='Imported From Attendance',
        default=False,
    )

    def _compute_amount(self):
        res = super(HrPayslipWorkedDays, self)._compute_amount()
        for worked_days in self.filtered(lambda wd: not wd.payslip_id.edited):
            if worked_days.payslip_id.wage_type == "hourly":
                worked_days.amount = worked_days.payslip_id.contract_id.hourly_wage * \
                    worked_days.number_of_hours if worked_days.is_paid else 0
            else:
                number_of_days = worked_days.number_of_days

                worked_days.amount = (worked_days.payslip_id.contract_id.contract_wage /
                                      30) * number_of_days if worked_days.is_paid else 0
                # if worked_days.code == 'WORK100':
                #     worked_days_lines = worked_days.payslip_id.worked_days_line_ids.filtered(lambda line: line.code != 'WORK100')
                #     worked_days.amount = worked_days.amount - sum(worked_days_lines.mapped('amount'))
                if worked_days.code == 'OUT':
                    worked_days.amount = 0.0

            if worked_days.is_leave_advance:
                worked_days.amount = - worked_days.amount
        return res
