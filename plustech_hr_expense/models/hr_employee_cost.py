from odoo import fields, models, api


class HrEmployeeCost(models.Model):
    _name = 'hr.employee.cost'
    _description = 'Employee Cost'

    employee_id = fields.Many2one('hr.employee')
    emp_number = fields.Char()
    department_id = fields.Many2one('hr.department')
    job_id = fields.Many2one('hr.job')
    work_location_id = fields.Many2one('hr.work.location')
    cost = fields.Float(string="Cost")
    date = fields.Date(string='Date')
    analytic_account = fields.Many2one('account.analytic.account', string="Cost Center")
    ref = fields.Char(string="Reference")
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company)

    @api.model
    def generate_daily_transactions(self):
        today = fields.Date.today()
        expenses = self.env['hr.employee.expense'].search([('effective_date', '<=', today),
                                                           ('end_date', '>=', today)])
        cost_vals = []
        for exp in expenses:
            analytic_account = exp.employee_id.department_id.analytic_account_id
            if self.env.company.employee_cost_center == 'location':
                analytic_account = exp.employee_id.work_location_id.analytic_account_id
            vals = {
                'employee_id': exp.employee_id.id,
                'emp_number': exp.employee_id.employee_number,
                'department_id': exp.employee_id.department_id.id,
                'job_id': exp.employee_id.job_id.id,
                'work_location_id': exp.employee_id.work_location_id.id,
                'cost': exp.amount / 30,
                'date': today,
                'ref': exp.expense_type_id.name,
                'analytic_account': analytic_account.id
            }
            cost_vals.append(vals)
        contracts = self.env['hr.contract'].search([('state', '=', 'open'), ('employee_id', '!=', False)])
        for contract in contracts:
            analytic_account = exp.employee_id.department_id.analytic_account_id
            if self.env.company.employee_cost_center == 'location':
                analytic_account = exp.employee_id.work_location_id.analytic_account_id
            vals = {
                    'employee_id': contract.employee_id.id,
                    'emp_number': contract.employee_id.employee_number,
                    'department_id': contract.employee_id.department_id.id,
                    'job_id': contract.employee_id.job_id.id,
                    'work_location_id': contract.employee_id.work_location_id.id,
                    'cost': contract.wage / 30,
                    'date': today,
                    'ref': 'Basic Salary',
                    'analytic_account': analytic_account.id
                }
            cost_vals.append(vals)
            for line in contracts.allowance_ids:
                vals = {
                    'employee_id': contract.employee_id.id,
                    'emp_number': contract.employee_id.employee_number,
                    'department_id': contract.employee_id.department_id.id,
                    'job_id': contract.employee_id.job_id.id,
                    'work_location_id': contract.employee_id.work_location_id.id,
                    'cost': line.allowance_amount / 30,
                    'date': today,
                    'ref': line.allowance_type.name,
                    'analytic_account': analytic_account.id
                }
                cost_vals.append(vals)

        self.create(cost_vals)
