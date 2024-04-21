from odoo import models, _


class BatchReportXls(models.AbstractModel):
    _name = 'report.plustech_hr_payroll.batch'
    _description = 'Payslip Batch Excel Report'
    _inherit = 'report.report_xlsx.abstract'

    def _get_allowances(self, batch_id):
        payslip = self.env['hr.payslip'].search([('payslip_run_id', '=', batch_id)])
        allowances = payslip.line_ids.mapped('salary_rule_id').filtered(lambda line: line.category_id.code in ['ALW','BASIC'])
        return allowances

    def _get_deductions(self, batch_id):
        payslip = self.env['hr.payslip'].search([('payslip_run_id', '=', batch_id)])
        deductions = payslip.line_ids.mapped('salary_rule_id').filtered(
            lambda line: line.category_id.code in ['DED'])
        return deductions

    def generate_xlsx_report(self, workbook, data, records):
        format0 = workbook.add_format({'font_size': 14, 'font_name': 'Arial', 'align': 'center','valign': 'vcenter', 'border': 2,
                                       'bold': True, 'bg_color': '#d9d9d9', 'color': 'black', 'bottom': True,
                                       'num_format': '#,##0.00'})
        format1 = workbook.add_format({'font_size': 14, 'font_name': 'Arial', 'align': 'vcenter', 'border': 2,
                                       'bold': True, 'bg_color': '#d9d9d9', 'color': 'black', 'bottom': True,
                                       'num_format': '#,##0.00'})
        format2 = workbook.add_format({'font_size': 12, 'font_name': 'Arial', 'align': 'center','valign': 'vcenter', 'border': 2,
                                       'bold': True,  'color': 'black', 'bottom': True,
                                       'num_format': '#,##0.00'})
        format3 = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 10,  'align': 'center',
             'valign': 'vcenter', 'bold': True, 'border': 2, 'num_format': '#,##0.00'})
        format4 = workbook.add_format({'font_size': 14, 'font_name': 'Arial', 'align': 'vcenter', 'border': 2,
                                       'bold': True, 'color': 'black', 'bottom': True,
                                       'num_format': '#,##0.00'})
        format5 = workbook.add_format(
            {'font_size': 12, 'font_name': 'Arial', 'align': 'center', 'valign': 'vcenter', 'border': 2,
             'bold': True, 'color': 'black', 'bottom': True, 'bg_color': '#d9d9d9',
             'num_format': '#,##0.00'})

        active_ids = records.ids
        batches = self.env['hr.payslip.run'].sudo().browse(active_ids)
        slip_ids = batches.slip_ids
        departments = []
        for department in slip_ids.department_id:
            if department.id not in departments:
                departments.append([department.id, department.name])
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
        net_salary_total = 0.0
        batch_total_allowance = 0.0
        batch_total_deduction = 0.0
        batch_totals = {}
        allowances = self._get_allowances(batches.id)
        deductions = self._get_deductions(batches.id)
        e_name = 2
        sheet.set_column(e_name, 9, 20)
        sheet.merge_range(e_name, 0, e_name+1, 0, _('No#'), format1)
        sheet.merge_range(e_name, 1, e_name+1, 1, _('Employee ID'), format1)
        sheet.merge_range(e_name, 2, e_name+1, 2, _('Employee Name'), format1)
        # sheet.merge_range(e_name, 3, e_name+1, 3, _('Basic Salary'), format1)
        sheet.merge_range(e_name, 3, e_name, len(allowances)+3, 'Allowances', format0)
        e_name += 1
        col = 4
        allowance_count = len(allowances)
        allowance_col = 3
        for allowance in allowances:
            sheet.write(e_name, allowance_col, allowance.name, format1)
            # sheet.set_column(e_name, p, len(allowance) * 10)
            allowance_col += 1
        sheet.write(e_name, allowance_col, 'Total Allowances', format1)
        col += allowance_count
        sheet.merge_range(e_name-1, col, e_name-1, len(deductions)+col, 'Deductions', format0)

        for ded in deductions:
            sheet.write(e_name, col, ded.name, format1)
            # sheet.set_column(e_name, p, len(allowance) * 10)
            col += 1
        sheet.write(e_name, col, 'Total Deductions', format1)
        col += 1
        sheet.merge_range(e_name-1, col, e_name, col, 'Net Salary', format1)
        col += 1
        sheet.merge_range(e_name-1, col, e_name, col, 'Signature', format1)

        e_name += 1
        for used_dept in departments:
            allowance_list = {line.name: 0.0 for line in allowances}
            deductions_list = {line.name: 0.0 for line in deductions}
            sheet.merge_range(e_name, 0, e_name, col,  used_dept[1], format4)
        #     # List report column headers:
        #
            e_name += 1
        #
        #     basic_salary = 0.0
            dept_net_salary = 0.0
            dept_net_total_allowance = 0.0
            dept_net_total_deduction = 0.0
            contract_count = 1

            for slip in slip_ids.filtered(lambda sl: sl.employee_id.department_id.id == used_dept[0]):
                alw_col = 3
                sheet.write(e_name, 0, str(contract_count), format3)
                sheet.write(e_name, 1, slip.employee_id.employee_number or '', format3)
                sheet.write(e_name, 2, slip.employee_id.name or '', format3)
                total_allowance = 0.0
                total_deduction = 0.0
                contract_count += 1
                for alw in allowances:
                    line = self.env['hr.payslip.line'].search([('salary_rule_id', '=', alw.id),
                                                               ('slip_id', '=', slip.id)])
                    if line:
                        sheet.write(e_name, alw_col, line.amount, format3)
                        allowance_list[alw.name] += line.amount
                        total_allowance += line.amount
                    else:
                        sheet.write(e_name, alw_col, 0.0, format3)
                    alw_col += 1
                sheet.write(e_name, alw_col, total_allowance, format3)
                alw_col += 1
                for ded in deductions:
                    line = self.env['hr.payslip.line'].search([('salary_rule_id', '=', ded.id),
                                                               ('slip_id', '=', slip.id)])
                    if line:
                        sheet.write(e_name, alw_col, line.amount, format3)
                        deductions_list[ded.name] += line.amount
                        total_deduction += line.amount
                    else:
                        sheet.write(e_name, alw_col, 0.0, format3)
                    alw_col += 1
                sheet.write(e_name, alw_col, total_deduction, format3)
                alw_col += 1
                sheet.write(e_name, alw_col, slip.net_wage or 0.0, format3)
                dept_net_salary += slip.net_wage
                dept_net_total_allowance += total_allowance
                dept_net_total_deduction += total_deduction
                alw_col += 1
                sheet.write(e_name, alw_col, '', format3)
                e_name += 1

            total_col = 3
            for t_alw in allowance_list:
                sheet.write(e_name, total_col, allowance_list[t_alw], format2)
                if t_alw in batch_totals:
                    batch_totals[t_alw] += allowance_list[t_alw]
                else:
                    batch_totals[t_alw] = allowance_list[t_alw]
                total_col += 1
            batch_totals['allowance_total'] = 0.0
            sheet.write(e_name, total_col, dept_net_total_allowance, format2)
            total_col += 1
            for t_ded in deductions_list:
                sheet.write(e_name, total_col, deductions_list[t_ded], format2)
                if t_ded in batch_totals:
                    batch_totals[t_alw] += deductions_list[t_ded]
                else:
                    batch_totals[t_ded] = deductions_list[t_ded]
                total_col += 1
            sheet.write(e_name, total_col, dept_net_total_deduction, format2)
            total_col += 1
            net_salary_total += dept_net_salary
            batch_total_allowance += dept_net_total_allowance
            batch_total_deduction += dept_net_total_deduction
            sheet.write(e_name, total_col, dept_net_salary, format2)
            sheet.write(e_name, total_col+1, '', format2)
            sheet.merge_range(e_name, 0, e_name, 2, _('Department Total'), format4)
            e_name += 1
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
        #     dept_count += 1
        # e_name -= 2
        sheet.merge_range(e_name, 0, e_name, 2, _('Total Salaries'), format1)
        col = 3
        for line in batch_totals:
            if line == 'allowance_total':
                sheet.write(e_name, col, batch_total_allowance, format5)
            else:
                sheet.write(e_name, col,  batch_totals[line], format5)
            col += 1
        sheet.write(e_name, total_col-1, batch_total_deduction, format5)
        sheet.write(e_name, total_col, net_salary_total, format5)
        sheet.write(e_name, total_col + 1, '', format5)


