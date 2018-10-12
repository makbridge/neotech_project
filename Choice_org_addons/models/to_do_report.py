from odoo import models, fields, api, _, SUPERUSER_ID
from odoo import tools
from datetime import datetime, date, time, timedelta
from StringIO import StringIO
import xlsxwriter as xls
import base64
import itertools
from xlsxwriter.utility import xl_rowcol_to_cell
import pytz
from dateutil.parser import parse
from odoo.exceptions import UserError, ValidationError
from collections import namedtuple
import math
from xlsxwriter.utility import xl_rowcol_to_cell


def nameBox(row, col,  row_abs=None, col_abs=None):
		cell = ''
		cell = xl_rowcol_to_cell(row, col)
		return cell

class ToDoReport(models.TransientModel):
    _name='todo.report'
    _description="To Do Report"	


    employee_id = fields.Many2one('res.users','Employee')
    date_to = fields.Date("To Date")
    date_from = fields.Date("From Date")
    to_do_excel_sheet = fields.Binary()
    file_name = fields.Char('Excel File', size=64)

    @api.multi
    def print_to_do_report(self):
        for rec in self:
            date_from=rec.date_from
            date_to=rec.date_to
            if not date_from:
                raise ValidationError(_('Please Enter From Date'))
            elif not date_to:
                raise ValidationError(_('Please Enter To Date'))
            elif date_from > date_to:
                raise ValidationError(_('Please Select Proper Date.'))

        fp = StringIO()
        workbook = xls.Workbook(fp)
        
        header_format = workbook.add_format({
                                        'bold': 1,
                                        'align': 'center',
                                        'valign': 'vcenter',
                                        'text_wrap':1,
                                        'font_name':'Verdana',
                                        'font_size':10,
                                        })
        data_format = workbook.add_format({
                                        'align': 'center',
                                        'valign': 'vcenter',
                                        'text_wrap':1,
                                        'font_name':'Verdana',
                                        'font_size':10,
                                        })
        
        no_data_format = workbook.add_format({
                                        'align': 'center',
                                        'valign': 'vcenter',
                                        'text_wrap':1,
                                        'font_name':'Verdana',
                                        'font_size':10,
                                        'font_color':'red',
                                        })
        
        merge_format = workbook.add_format({
                                        'align': 'center',
                                        'valign': 'vcenter',
                                        'text_wrap':1,
                                        'font_name':'Verdana',
                                        'font_size':10,
                                        'bold' : 1,
                                        })
        title_format = workbook.add_format({
                                        'align': 'center',
                                        'valign': 'vcenter',
                                        'text_wrap':1,
                                        'font_name':'Verdana',
                                        'font_size':14,
                                        'bold' : 1,})
        
        bold = workbook.add_format({'bold': True , 'bg_color':'#808080','font_color':'black'})
        file_name = 'To Do Reports.xlsx'
        report_name = 'To Do Report'
        worksheet = workbook.add_worksheet(report_name)

        title = "To Do Report"
        worksheet.merge_range(1, 1, 1, 8,title,title_format)
        worksheet.write('A3:A3','Sr. No.',header_format)
        worksheet.write('B3:B3','Task Type',header_format)
        worksheet.write('C3:C3','Task Priority',header_format)
        worksheet.write('D3:D3','Task Status',header_format)
        worksheet.write('E3:E3','Deadline',header_format)
        worksheet.write('F3:F3','Allocated Time',header_format)
        worksheet.write('G3:G3','% of Completion',header_format)
        worksheet.write('H3:H3','Task Name',header_format)
        worksheet.write('I3:I3','Comments',header_format)


        myDate = date.today()
        today_date =  str(myDate.month)+ "/" + str(myDate.day) + "/" + str(myDate.year)
        todays_date = datetime.today().strftime('%Y-%m-%d')
        task_search_ids = self.env['task.management'].search([('estimated_start_date','>=',self.date_from),
            ('estimated_start_date','<=',self.date_to),('assigned_to','=',self.employee_id.id),('state','!=',['completed']),
            ('to_do_task','=',True)])
        print "\n\n_______task_search_ids_______",task_search_ids

        worksheet.merge_range(0,5,0,8,'From ' + date_from+' to '+date_to,title_format)


        row=3
        sr_no = 0

        for i in task_search_ids:
            col = 0

            employee = i.assigned_to.name
            worksheet.merge_range(0, 0, 0, 4, "Employee: "+employee,title_format)
            for l in i.task_history :
                    date1 = l.task_history_date
                    date2 = datetime.today().strftime('%Y-%m-%d')
                    
                    if date1 < date2 :
                        percent = 0.0
                        percent = l.task_percent_completion
                        i.initial_completion = l.task_percent_completion

            comment = ''
            for j in i.task_manual_time:
                if j.task_manual_comments:
                    comment = j.task_manual_comments
                            
            i.current_completion = i.percantage_task_completion
            difference = 0.0
            if i.current_completion > 0.0:
                    difference = float(i.current_completion) - float(i.initial_completion)

            task_priority = dict(i._fields['task_priority'].selection).get(i.task_priority)
            task_type = dict(i._fields['task_type'].selection).get(i.task_type)
            task_status = dict(i._fields['state'].selection).get(i.state)
            task_name = i.name if i.name else " "
            deadline = i.deadline

            alloted_time = 0.0
            if i.task_allocated_time : 
                    alloted_time = i.task_allocated_time*3600
                    alloted_time_delta = timedelta(seconds=alloted_time)
                    alloted_time = str(timedelta(seconds=alloted_time))

            sr_no=sr_no+1
                
            worksheet.write(row,col,sr_no,data_format)
            worksheet.write(row,col+1,task_type,data_format)
            worksheet.write(row,col+2,task_priority,data_format)
            worksheet.write(row,col+3,task_status,data_format)
            worksheet.write(row,col+4,deadline,data_format)
            if i.task_allocated_time :
                alloted_time1 = datetime.strptime(alloted_time,'%H:%M:%S')
                alloted_time2 = date.strftime(alloted_time1, '%H:%M')
                worksheet.write(row,col+5,alloted_time2,data_format)
            worksheet.write(row,col+6,difference,data_format)
            worksheet.write(row,col+7,task_name,data_format)
            worksheet.write(row,col+8,comment,data_format)
            row +=1    

        workbook.close()
        out=base64.encodestring(fp.getvalue())
        data = (file_name,base64.b64decode(out))    
        cd=self.write({'to_do_excel_sheet':out, 'file_name':file_name})
        return True