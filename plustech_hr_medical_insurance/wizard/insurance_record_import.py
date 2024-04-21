# -*- coding:utf-8 -*-
##############################################################################
#    Description: Employee Insurance Data Lines Import                      #
#    Author: Plus Tech Software                                            #
#    Date: Aug 2022 -  Till Now                                              #
##############################################################################

import base64
import xlrd

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ImportInsuranceRecord(models.TransientModel):
    _name = 'import.insurance.record'

    files = fields.Binary(string="Excel File")
    datas_fname = fields.Char('File Name')

    def import_file(self):
        employee_obj = self.env['hr.employee']
        employee_record_obj = self.env['employee.insurance.record']
        model = self._context.get('active_model')
        record_id = self._context.get('active_id')
        record = self.env[model].browse(record_id)
        try:
            workbook = xlrd.open_workbook(file_contents=base64.b64decode(self.files))
        except:
            raise ValidationError("Please select your .xls/xlsx file.")
        sheet_name = workbook.sheet_names()
        sheet = workbook.sheet_by_name(sheet_name[0])
        nrows = sheet.nrows
        row = 1
        while row < nrows:
            employee_id = employee_obj.search([('employee_number', '=', str(int(sheet.cell(row, 0).value)))])
            if not employee_id:
                raise ValidationError(
                    _('Employee ID %s is at row number %s. is not exist please check.' % (
                        sheet.cell(row, 0).value, row + 1)))
            # get member name
            name = sheet.cell(row, 1).value
            if not name:
                raise ValidationError(
                    _('Name is invalid at row number %s. Please check.' % (sheet.cell(row, 1).value, row + 1)))
                # get member age
            age = sheet.cell(row, 2).value
            if not age or age <= 0:
                raise ValidationError(
                    _('Member age is invalid at row number %s. Please check.' % (row + 1)))
            # get member cost
            amount = sheet.cell(row, 3).value
            if amount and type(amount) != float:
                raise ValidationError(
                    _('Amount is invalid at row number %s. Please check.' % (row + 1)))
            # get member type
            member_type = sheet.cell(row, 4).value
            if member_type not in ['employee', 'dependent']:
                raise ValidationError(
                    _('Member Type is invalid at row number %s. Please check.' % (row + 1)))
            # get relation type
            relation = sheet.cell(row, 6).value

            if member_type != 'employee' and relation not in ['father', 'mother', 'daughter', 'son', 'spouse']:
                raise ValidationError(
                    _('Relation Type is invalid at row number %s. Please check.' % (row + 1)))

            insurance_class = sheet.cell(row, 5).value
            row = row + 1
            vals = {
                'employee_id': employee_id.id,
                'name': name,
                'amount': amount,
                'parent_id': record.id,
                'member_type': member_type,
                'insurance_class': insurance_class,
                'age': int(age), 'relation': relation
            }
            employee_record_obj.create(vals)

