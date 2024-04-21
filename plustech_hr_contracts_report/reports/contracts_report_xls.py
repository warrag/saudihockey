from odoo import models, _


class ContractsReport(models.AbstractModel):
    _name = 'report.plustech_hr_contract.contract'
    _description = 'Contracts Excel Report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, records):
        format1 = workbook.add_format({'font_size': 14, 'font_name': 'Arial', 'align': 'vcenter', 'border': 2,
                                       'bold': True, 'bg_color': '#d9d9d9', 'color': 'black', 'bottom': True,
                                       'num_format': '#,##0.00'})
        format3 = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 10,  'align': 'center',
             'valign': 'vcenter', 'bold': True, 'border': 2, 'num_format': '#,##0.00'})
        format4 = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 10, 'align': 'center',
             'valign': 'vcenter', 'bold': True, 'border': 2, 'num_format': 'dd/mm/yyyy'})

        active_ids = records.employee_ids.mapped('contract_id').ids
        contracts = self.env['hr.contract'].sudo().browse(active_ids)
        departments = []
        for department in contracts.department_id:
            if department.id not in departments:
                departments.append([department.id, department.name])
        dept_count = 1
        report_name = _('Total Employees Report ' + str(self.env.company.name))
        sheet = workbook.add_worksheet(_('Total Employees Report'))
        if self.env.user.lang == 'ar_001':
            sheet.right_to_left()
        title_style = workbook.add_format({
            'font_name': 'Arial',
            'font_size': 16,
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'border': 0,
            'bg_color': '#d9d9d9'
        })
        basic_salary_total = 0.0
        net_salary_total = 0.0
        allowance_totals = {}
        allowance_categories = contracts.allowance_ids.mapped('allowance_type').category_id
        for line in allowance_categories:
            allowance_totals[line.name] = 0.0
        sheet.merge_range(0, 0, 0, len(allowance_categories)+11, report_name, title_style)
        e_name = 2
        for used_dept in departments:
            sheet.merge_range(e_name, 0, e_name, len(allowance_categories)+11,  used_dept[1], format1)
            e_name += 1
            # List report column headers:
            sheet.set_column(e_name, 9, 20)
            sheet.write(e_name, 0, _('No#'), format1)
            sheet.write(e_name, 1, _('Employee ID'), format1)
            sheet.write(e_name, 2, _('Employee Name'), format1)
            sheet.write(e_name, 3, _('Manager'), format1)
            sheet.write(e_name, 4, _('National ID Number'), format1)
            sheet.write(e_name, 5, _('Birth Date'), format1)
            sheet.write(e_name, 6, _('Job Position'), format1)
            sheet.write(e_name, 7, _('Nationality'), format1)
            sheet.write(e_name, 8, _('Gender'), format1)
            sheet.write(e_name, 9, _('Join Date'), format1)
            sheet.write(e_name, 10, _('Basic Salary'), format1)
            allowance_count = 11
            allowance_list = []
            allowances = contracts.allowance_ids.mapped('allowance_type').category_id
            for allowance in allowances:
                sheet.write(e_name, allowance_count, allowance.name, format1)
                allowance_list.append([allowance_count, allowance, 0.0, 0.0])
                allowance_count += 1
            sheet.write(e_name, allowance_count, _('Net Salary'), format1)
            e_name += 1

            basic_salary = 0.0
            net_salary = 0.0
            contract_count = 1
            for contract in contracts.filtered(lambda c: c.department_id.id == used_dept[0]):
                gender = dict(contract.employee_id.fields_get(allfields=['gender'])['gender']['selection'])[contract.employee_id.gender] if contract.employee_id.gender else ''
                sheet.write(e_name, 0, str(contract_count), format3)
                sheet.write(e_name, 1, contract.employee_id.employee_number or '', format3)
                sheet.write(e_name, 2, contract.employee_id.name or '', format3)
                sheet.write(e_name, 3, contract.employee_id.parent_id.name or '', format3)
                sheet.write(e_name, 4, contract.employee_id.identification_id or '', format3)
                sheet.write(e_name, 5, contract.employee_id.birthday or '', format4)
                sheet.write(e_name, 6, contract.job_id.name or '', format3)
                sheet.write(e_name, 7, contract.employee_id.country_id.name or '', format3)
                sheet.write(e_name, 8, gender or '', format3)
                sheet.write(e_name, 9, contract.employee_id.join_date or '', format4)
                sheet.write(e_name, 10, contract.wage or '', format3)
                e_name += 1
                contract_count += 1
                basic_salary += contract.wage
                net_salary += contract.monthly_yearly_costs
                for line in contract.allowance_ids:
                    for categ in allowance_list:
                        if line.allowance_type.category_id == categ[1]:
                            sheet.write(
                                e_name-1, categ[0], line.allowance_amount, format3)
                            categ[2] += line.allowance_amount
                for categ in allowance_list:
                    if categ[1].id not in contract.allowance_ids.allowance_type.category_id.ids:
                        sheet.write(
                            e_name - 1, categ[0], 0.0, format3)
                sheet.write(e_name-1, allowance_count, contract.monthly_yearly_costs or '', format3)
            sheet.merge_range(e_name, 0, e_name+1, 7, _('Department Total'), format1)
            sheet.merge_range(e_name, 8,e_name,9, _('Department Employees'), format1)
            sheet.merge_range(e_name+1, 8,e_name+1,9, str(contract_count), format1)
            sheet.merge_range(e_name, 10, e_name+1, 10, basic_salary, format1)
            basic_salary_total += basic_salary
            net_salary_total += net_salary
            for line in allowance_list:
                sheet.merge_range(e_name, line[0], e_name + 1, line[0], line[2], format1)
                allowance_totals[line[1].name] += line[2]
            sheet.merge_range(e_name, allowance_count, e_name + 1, allowance_count, net_salary, format1)
            e_name += 3
            sheet.set_column('A:A', 16)
            sheet.set_column('B:B', 20)
            sheet.set_column('D:D', 16)
            sheet.set_column('E:E', 20)
            sheet.set_column('F:F', 14)
            sheet.set_column('C:C', 18)
            sheet.set_column('G:G', 12)
            sheet.set_column('I:I', 16)
            sheet.set_column('J:J', 16)
            sheet.set_column('K:K', 14)
            sheet.set_column('L:L', 16)
            sheet.set_row(0, 50)
            dept_count += 1
        e_name -= 2
        sheet.merge_range(e_name+1, 0, e_name + 1, 7, _('Total Employees'), format1)
        sheet.merge_range(e_name+2, 0, e_name + 2, 7, _('Total Salaries'), format1)
        sheet.merge_range(e_name + 1, 8, e_name + 2, 9, str(len(contracts)), format1)
        sheet.merge_range(e_name + 1, 10, e_name + 2, 10, basic_salary_total, format1)
        allowance_count = 11
        for line in allowance_totals:
            sheet.merge_range(e_name+1, allowance_count, e_name+2, allowance_count, allowance_totals[line], format1)
            allowance_count += 1
        sheet.merge_range(e_name + 1, allowance_count, e_name + 2, allowance_count, net_salary_total, format1)

