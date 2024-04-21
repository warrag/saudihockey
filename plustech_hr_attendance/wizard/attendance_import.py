# -*- coding:utf-8 -*-
##############################################################################
#    Description: Sales and Purchase Order Lines Import                      #
#    Author: IntelliSoft Software                                            #
#    Date: Aug 2015 -  Till Now                                              #
##############################################################################

import base64
import xlrd

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT,DEFAULT_SERVER_DATE_FORMAT


# import purchase order line(s) from Excel file
class ImportSpare(models.TransientModel):
    _name = 'import.attendance'
    _description = 'Import Attendance'

    files = fields.Binary(string="Excel File")
    datas_fname = fields.Char('File Name')

    # import sale order line(s) from excel file
    def import_file(self):
        employee_obj = self.env['hr.employee']
        attendance_log_obj = self.env['attendance.log']
        attendance_obj = self.env['hr.attendance']
        try:
            workbook = xlrd.open_workbook(file_contents=base64.decodestring(self.files))
        except:
            raise ValidationError("Please select your .xls/xlsx file.")
        sheet_name = workbook.sheet_names()
        sheet = workbook.sheet_by_name(sheet_name[0])
        nrows = sheet.nrows
        row = 0
        while (row < nrows):
            print(str(int(sheet.cell(row, 0).value)))
            # get product and description
            employee_id = employee_obj.search([('device_id', '=', str(int(sheet.cell(row, 0).value)))])
            if not employee_id:
                raise ValidationError(
                    _('Biometric Device ID %s is invalid at row number %s. Please check.' % (
                        sheet.cell(row, 0).value, row + 1)))
            # get time
            try:
                time = sheet.cell(row, 1).value
            except:
                raise ValidationError(
                    _('Event time is invalid at row number %s. Please check.' % (sheet.cell(row, 1).value, row + 1)))
            # get event type
            try:
                event_type = int(sheet.cell(row, 3).value)
            except:
                raise ValidationError(
                    _('Event type is invalid at row number %s. Please check.' % (
                        sheet.cell(row, 4).value, row + 1)))
            row = row + 1
            a1_as_datetime = datetime(*xlrd.xldate_as_tuple(time, workbook.datemode))
            event_date = a1_as_datetime + relativedelta(hours=-3)
            vals = {
                'employee_id': employee_id.id,
                'event_time': event_date,
                'event_type': str(event_type),
            }
            attendance_log_obj.create(vals)
        check_in_ids = attendance_log_obj.search([('attendance_id', '=', False), ('event_type', '=', '0')],
                                                 order='date ASC,event_time DESC')
        print(check_in_ids)
        if check_in_ids:
            for log in check_in_ids:
                vals = {}
                check_out = attendance_log_obj.search([('attendance_id', '=', False), ('event_type', '=', '1'),
                                                       ('date', '=', log.date),
                                                       ('employee_id', '=', log.employee_id.id)], order='event_time ASC')
                pre_attendance = attendance_obj.search([('employee_id', '=', log.employee_id.id), ('check_out', '=', False), ('check_in', '<', log.event_time)], limit=1)
                print(check_out,log.event_time)
                if check_out:
                    if check_out[-1].event_time < log.event_time and len(check_out) == 1:
                        pre_attendance.check_out = check_out[-1].event_time

                        vals = {
                            'employee_id': log.employee_id.id,
                            'check_in': log.event_time,
                            'check_out': False,
                        }
                    else:
                        vals = {
                            'employee_id': log.employee_id.id,
                            'check_in': log.event_time,
                            'check_out': check_out[-1].event_time,
                        }
                log.attendance_id = attendance_obj.create(vals).id
