from odoo import models
import string
from datetime import date


class AlrajhiWPSPayrollReport(models.AbstractModel):
    _name = 'report.xlsx_payroll_report.alrajhi_wps'
    _description = 'Alrajhi WPS Payroll Excel Report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        print(data)
        format1 = workbook.add_format({'font_size': 14, 'font_name': 'Arial', 'align': 'vcenter', 'border': 2,
                                       'bold': True, 'bg_color': '#000080', 'color': 'white', 'bottom': True, })
        format3 = workbook.add_format(
            {'font_name': 'Arial', 'font_size': 10,  'align': 'center',
                'valign': 'vcenter', 'bold': True, 'border': 2, 'num_format': '#,##0.00'})


        # Fetch available salary rules:
        active_id = data['context'].get('active_id')
        lines = self.env['hr.payslip.run'].sudo().browse(active_id)
        used_structures = []
        for sal_structure in lines.slip_ids.struct_id:
            if sal_structure.id not in used_structures:
                used_structures.append([sal_structure.id, sal_structure.name])
        # Logic for each workbook, i.e. group payslips of each salary structure into a separate sheet:
        struct_count = 1
        for used_struct in used_structures:
            # Generate Workbook
            sheet = workbook.add_worksheet(
                str(struct_count) + ' - ' + str(used_struct[1]))
            cols = list(string.ascii_uppercase) + ['AA', 'AB', 'AC', 'AD', 'AE', 'AF', 'AG', 'AH', 'AI', 'AJ',
                                                   'AK', 'AL', 'AM', 'AN', 'AO', 'AP', 'AQ', 'AR', 'AS', 'AT', 'AU',
                                                   'AV', 'AW', 'AX', 'AY', 'AZ']
            rules = []
            col_no = 6
            # Fetch available salary rules:
            for item in lines.slip_ids.struct_id.rule_ids.filtered(lambda l: l.code in ['BASIC', 'HALW']):
                if item.struct_id.id == used_struct[0]:
                    row = [None, None, None, None, None]
                    row[0] = col_no
                    row[1] = item.code
                    row[2] = item.name
                    col_title = str(cols[col_no]) + ':' + str(cols[col_no])
                    row[3] = col_title
                    if len(item.name) < 8:
                        row[4] = 12
                    else:
                        row[4] = len(item.name) + 2
                    rules.append(row)
                    col_no += 1
            col_no += 2
            # print('Salary rules to be considered for structure: ' + used_struct[1])
            # print(rules)

            # Report Details:
            for item in lines.slip_ids:
                if item.struct_id.id == used_struct[0]:
                    batch_period = str(item.date_from.strftime(
                        '%B %d, %Y')) + '  To  ' + str(item.date_to.strftime('%B %d, %Y'))
                    company_id = item.company_id
                    break

            # List report column headers:
            sheet.write(0, 0, 'Bank #', format1)
            sheet.write(0, 1, 'Account #', format1)
            sheet.write(0, 2, 'Employee Name', format1)
            sheet.write(0, 3, 'Employee Number', format1)
            sheet.write(0, 4, 'National ID Number', format1)
            sheet.write(0, 5, 'Salary', format1)
            sheet.write(0, 10, 'Employee Remarks', format1)
            sheet.write(0, 11, 'Employee Department', format1)
            for rule in rules:
                sheet.write(0, rule[0], rule[2], format1)
            sheet.write(0, 8, 'Other Earnings', format1)
            sheet.write(0, 9, 'Deductions', format1)

            # Generate names, dept, and salary items:
            x = 1
            e_name = 1
            has_payslips = False
            total_deductions = 0.0
            amount_total = 0.0
            for slip in lines.slip_ids:
                if lines.slip_ids:
                    if slip.struct_id.id == used_struct[0]:
                        has_payslips = True
                        sheet.write(e_name, 0, slip.employee_id.bank_account_id.bank_id.name or '', format3)
                        sheet.write(e_name, 1, slip.employee_id.bank_account_id.acc_number or '', format3)
                        sheet.write(e_name, 2, slip.employee_id.name, format3)
                        sheet.write(e_name, 3, slip.employee_id.employee_number or '', format3)
                        allowance = 0.0
                        deduction = 0.0
                        net = 0.0
                        for line in slip.line_ids:
                            for rule in rules:
                                if line.code == rule[1]:
                                    if line.amount > 0:
                                        sheet.write(
                                            x, rule[0], line.amount, format3)
                                        net += line.amount
                                    else:
                                        sheet.write(
                                            x, rule[0], line.amount, format3)
                            if line.category_id.code == 'ALW' and line.salary_rule_id.code != 'HALW':
                                allowance += line.amount
                            if line.category_id.code == 'DED':
                                deduction += line.amount
                        sheet.write(e_name, 8, allowance, format3)
                        sheet.write(e_name, 9, abs(deduction), format3)

                        total_deductions += deduction
                        net += allowance
                        sheet.write(e_name, 4, slip.employee_id.identification_id or '', format3)
                        sheet.write(e_name, 5, net, format3)
                        sheet.write(e_name, 10, slip.number or '', format3)
                        sheet.write(e_name, 11, slip.employee_id.department_id.name or '', format3)
                        amount_total += net

                        x += 1
                        e_name += 1
            # set width and height of colmns & rows:
            sheet.set_column('A:A', 16)
            sheet.set_column('B:B', 20)
            sheet.set_column('D:D', 16)
            for rule in rules:
                sheet.set_column(rule[3], rule[4])
            sheet.set_column('E:E', 20)
            sheet.set_column('F:F', 14)
            sheet.set_column('C:C', 18)
            sheet.set_column('G:G', 12)
            sheet.set_column('I:I', 16)
            sheet.set_column('J:J', 16)
            sheet.set_column('K:K', 14)
            sheet.set_column('L:L', 16)
            sheet.set_row(0, 50)
            struct_count += 1
