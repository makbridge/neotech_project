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


class report_excel(models.TransientModel):
    _name = 'report.excel'
    _description = "Task Report"
    
    employee_id = fields.Many2one('res.users','Employee', default=lambda self: self.env.user)
    reviewer_id1 = fields.Many2one('res.user', 'Reviewer')


    date_to = fields.Date("To Date")
    date_from = fields.Date("From Date")
   
    excel_sheet = fields.Binary()
    file_name = fields.Char('Excel File', size=64)
    excel_sheet1 = fields.Binary()
    
    
    
    @api.multi
    def print_task_report(self):
        
        for rec in self:
            date_from=rec.date_from
            date_to=rec.date_to
           
            if not date_from:
                raise ValidationError(_('Please Enter From Date'))
            elif not date_to:
                raise ValidationError(_('Please Enter To Date'))
            elif date_from > date_to:
                raise ValidationError(_('Please Select Proper Date.')) 


        reviewer_name = []
        employee_name = ''
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
                                            })

        title_format = workbook.add_format({
                                        'align': 'center',
                                        'valign': 'vcenter',
                                        'text_wrap':1,
                                        'font_name':'Verdana',
                                        'font_size':14,
                                        'bold' : 1,})
        
        bold = workbook.add_format({'bold': True , 'bg_color':'#808080','font_color':'black'})
        file_name = 'Task Reports.xlsx'
        report_name = 'Task Status wise-Not Started'
        worksheet = workbook.add_worksheet(report_name)
        worksheet.set_column('A:A', 15)
        worksheet.set_column('B:B', 15)
        worksheet.set_column('C:C', 15)
        worksheet.set_column('D:D', 15)
        worksheet.set_column('E:E', 15)
        worksheet.set_column('F:F', 15)
        worksheet.set_column('G:G', 15)
        worksheet.set_column('H:H', 15)
        worksheet.set_column('I:I', 15)
        worksheet.set_column('J:J', 15)
       
        
        title='Task Wise Performed' 
        # date = datetime.now().strftime('%Y-%m-%d')
        worksheet.merge_range(0, 2, 0, 6,title,title_format)
        title='Task Status wise report- Not Started'
        employee_name = self.employee_id.name
        
        worksheet.write('A2:A2',title,header_format)
        worksheet.write('A3:A3','S No',header_format)
        worksheet.write('B3:B3','Task Priority',header_format)
        worksheet.write('C3:C3','Task Type',header_format)
        worksheet.write('D3:D3','Task Name',header_format)
        worksheet.write('E3:E3','Start Date',header_format)
        worksheet.write('F3:F3','Task Status',header_format)
        worksheet.write('G3:G3','Deadline',header_format)
        worksheet.write('H3:H3','Allotted Time  for the day',header_format)
        worksheet.write('I3:I3','Delay',header_format)
        worksheet.write('J3:J3','Comments',header_format)
        
        task_search_ids = self.env['task.management'].search([('estimated_start_date','>=',self.date_from),('estimated_start_date','<=',self.date_to),('assigned_to','=',self.employee_id.id),('state','in',['draft'])])
        # for z in task_search_ids:
        #         if z.reviewer.name:
        #                 reviewer_name.append(z.reviewer.name)
        # reviewer_name = list(set(reviewer_name))
        # r_name = ''
        # for c in reviewer_name:
        #     r_name = r_name + ', ' + c
        # 
        # employee_name = employee_name + '/ ' + r_name
        # worksheet.write('A1:A1',employee_name,header_format)
        worksheet.merge_range(0,7,0,10,'From ' + date_from+' to '+date_to,title_format)

        row1=1
        row=3
        col=0
        sr_no=0
        col3=0
        all_comment = ''
        
        for i in task_search_ids:
                temp_count = 0
                col=0
                temp_row = 0
        
                employee = i.assigned_to.name
                worksheet.merge_range(0, 0, 0, 1, "Employee: "+employee,title_format)
                if i.reviewer:
                    reviewer = i.reviewer.name
                    worksheet.merge_range(0, 11, 0, 15, "Reviewer: "+reviewer,title_format)
               
                task_priority = dict(i._fields['task_priority'].selection).get(i.task_priority)
                task_type = dict(i._fields['task_type'].selection).get(i.task_type)
                # task_type = i.task_type if i.task_type else " "
                task_name = i.name if i.name else " "
                start_date = i.estimated_start_date
                
                user_pool = self.env['res.users']
                user_brws = user_pool.browse(SUPERUSER_ID)
                
                start_tz = pytz.utc.localize(parse(start_date))
                
                start_format = start_tz.strftime ("%Y-%m-%d")
               
                # task_status = i.state
                task_status = dict(i._fields['state'].selection).get(i.state)
                deadline = i.deadline
                alloted_time = 0.0
                if i.task_allocated_time : 
                    alloted_time = i.task_allocated_time*3600
                    alloted_time = str(timedelta(seconds=alloted_time))
                
                myDate = date.today()    
                dateStr = str(myDate.year) +"-" + str(myDate.month)+ "-" + str(myDate.day)
                
                start_date = datetime.strptime(dateStr,'%Y-%m-%d')
                delay = 0.0
                if i.deadline:
                    end_date = datetime.strptime(i.deadline,'%Y-%m-%d')
                    diff = ''
                    if end_date < start_date:
                       diff = start_date - end_date
                       delay = diff.days
                manual_time = 0.0
                total_seconds = 0.0
                comment = []
                for j in i.task_manual_time:
                            
                    date1 = j.task_manual_date
                    date2 = datetime.today().strftime('%Y-%m-%d')
                    if date1 == date2 :
                        manual_time += j.task_manual_time
                        comment.append(str(j.task_manual_comments if j.task_manual_comments else ''))
                        all_comment = list(set(comment))
                        all_comment = ', '.join(all_comment)
                    
                            
                # for p in i.comment_id:
                #     comment = p.comments
               
                sr_no=sr_no+1
                
               
                worksheet.write(row,col,sr_no,data_format)
                # col += 1
                worksheet.write(row,col+1,task_priority,data_format)
                # col += 1
                worksheet.write(row,col+2,task_type,data_format)
                # col += 1
                worksheet.write(row,col+3,task_name,data_format)
                # col += 1
                worksheet.write(row,col+4,start_format,data_format)
                # col += 1
                worksheet.write(row,col+5,task_status,data_format)
                # col += 1
                worksheet.write(row,col+6,deadline,data_format)
                # col += 1
                if i.task_allocated_time :
                    alloted_time1 = datetime.strptime(alloted_time,'%H:%M:%S')
                    alloted_time2 = date.strftime(alloted_time1, '%H:%M')
                    worksheet.write(row,col+7,alloted_time2,data_format)
                # col += 1
                worksheet.write(row,col+8,delay,data_format)
                # col += 1
        
        
                # worksheet.write(row,col+9,)
                worksheet.write(row,col+9,all_comment,data_format)
                # col += 1
                row +=1
        
        
        # report_name = 'Task Status wise-In Progress'
        # worksheet = workbook.add_worksheet(report_name)
       
          
          
        title='Task Status wise report- In Progress' 
        worksheet.write(row+1,col,title,header_format)
                 
                    
        
        worksheet.write(row+2,col,'S No',header_format)
        worksheet.write(row+2,col+1,'Task Priority',header_format)
        worksheet.write(row+2,col+2,'Task Type',header_format)
        worksheet.write(row+2,col+3,'Task Name',header_format)
        worksheet.write(row+2,col+4,'Start Date',header_format)
        worksheet.write(row+2,col+5,'End Date',header_format)
        worksheet.write(row+2,col+6,'Task Status',header_format)
        worksheet.write(row+2,col+7,'Deadline',header_format)
        worksheet.write(row+2,col+8,'Allotted Time  for the day',header_format)
        worksheet.write(row+2,col+9,'Cummulative Time',header_format)
        worksheet.write(row+2,col+10,'Timed Time for day',header_format)
        worksheet.write(row+2,col+11,'Manual Time for the day',header_format)
        worksheet.write(row+2,col+12,'Overlap Time for the day',header_format)
        worksheet.write(row+2,col+13,'Delay',header_format)
        worksheet.write(row+2,col+14,'Reason for Delay',header_format)
        worksheet.write(row+2,col+15,'Comments',header_format)
        
        task_search_ids = self.env['task.management'].search([('estimated_start_date','>=',self.date_from),('estimated_start_date','<=',self.date_to)
            ,('assigned_to','=',self.employee_id.id),('state','in',['in_progress'])])
        sr_no=0
      
        for i in task_search_ids:
                temp_count = 0
                col=0
                temp_row = row+1
                total_second = 0.0
                for l in i.task_history :
                        
                        date1 = l.task_history_date
                        date2 = datetime.today().strftime('%Y-%m-%d')
                        
                        if date1 == date2 :   
                            total_second += l.task_spend_time
                
                overlap_time = 0.0
                overlap_time1 =0.0
                overlap_time_delta = timedelta(minutes=0)
                overlap_total = timedelta(minutes=0)
                comment  = []
                all_comment = ''
                a=[]
                for j in i.task_manual_time:
                    for l in i.task_history :
                        date1 = l.task_history_date
                        date2 = datetime.today().strftime('%Y-%m-%d')
                        date3 = j.task_manual_date
                        if date1 == date2:
                        
                            start = l.task_start_time
                            stop = l.task_stop_time
                            start1 = j.task_start_time
                            # start2 = datetime.strptime(str(start1), '%H.%M')
                            stop1 = j.task_end_time
                            # stop2 = datetime.strptime(str(stop1), '%H.%M')
                            # print "\n\n____stop2_____--",stop2
                            Range = namedtuple('Range', ['start', 'end'])
                            r1 = Range(start=start, end=stop)
                            r2 = Range(start=start1, end=stop1)
                            latest_start = max(r1.start, r2.start)
                            earliest_end = min(r1.end, r2.end)
                            if r1.start <= r2.start and r1.end >= r2.start or r1.start <= r2.end and r1.end >= r2.end:
                                delta = abs(latest_start - earliest_end)
                                delta = delta*60
                                overlap_time = str(timedelta(minutes=delta)).rsplit(':', 1)[0]
                                overlap_time_delta = timedelta(minutes=delta)
                                overlap_total += overlap_time_delta
                                # comment.append(str(j.task_manual_comments))
                                # all_comment = list(set(comment))
                                # all_comment = ', '.join(all_comment)
                            
                            if r1.start >= r2.start and r1.end <= r2.start or r1.start >= r2.end and r1.end <= r2.end:
                                delta = abs(latest_start - earliest_end)
                                delta = delta*60
                                overlap_time = str(timedelta(minutes=delta)).rsplit(':', 1)[0]
                                overlap_time_delta = timedelta(minutes=delta)
                                overlap_total += overlap_time_delta
                                # comment.append(str(j.task_manual_comments))
                                # all_comment = list(set(comment))
                                # all_comment = ', '.join(all_comment)

                    comment.append(str(j.task_manual_comments if j.task_manual_comments else ''))
                    all_comment = list(set(comment))
                    all_comment = ', '.join(all_comment)

                time_spent = i.x_time_spent
                
                # if i.time_spent:
                #     print "\n\n___________i.time_spent__________",i.time_spent
                #     time_spent = datetime.strptime(str(i.time_spent), '%H:%M')
                # else:
                #     time_spent = datetime.strptime(str("00:00"), '%H:%M')
                if overlap_time == 0.0:                    
                    overlap_time1 = date.strftime(datetime.strptime(str(overlap_total), '%H:%M:%S'), '%H:%M')
                else:
                    overlap_time1 = date.strftime(datetime.strptime(str(overlap_total), '%H:%M:%S'), '%H:%M')
                
                task_priority = dict(i._fields['task_priority'].selection).get(i.task_priority)
                task_type = dict(i._fields['task_type'].selection).get(i.task_type)
                task_status = dict(i._fields['state'].selection).get(i.state)
                task_name = i.name if i.name else " "
                start_date = i.estimated_start_date
                end_date = i.estimated_end_date
                user_pool = self.env['res.users']
                user_brws = user_pool.browse(SUPERUSER_ID)
                
                start_tz = pytz.utc.localize(parse(start_date))
                
                start_format = start_tz.strftime ("%Y-%m-%d")
                stop_tz = pytz.utc.localize(parse(end_date))
                
                stop_format = stop_tz.strftime ("%Y-%m-%d")
               
                deadline = i.deadline
                alloted_time = 0.0
                if i.task_allocated_time : 
                        alloted_time = i.task_allocated_time*3600
                        alloted_time = str(timedelta(seconds=alloted_time))
                
                myDate = date.today()    
                dateStr = str(myDate.year) +"-" + str(myDate.month)+ "-" + str(myDate.day)
                
                start_date = datetime.strptime(dateStr,'%Y-%m-%d')
                delay = 0
                if i.deadline:
                    end_date = datetime.strptime(i.deadline,'%Y-%m-%d')
                    diff = ''
                    if end_date < start_date:
                       diff = start_date - end_date
                       delay = diff.days
                manual_time = 0.0
                total_seconds = 0.0
                for j in i.task_manual_time:
                        
                    date1 = j.task_manual_date
                    date2 = datetime.today().strftime('%Y-%m-%d')
                    if date1 == date2 :
                        manual_time += j.task_manual_time
                        
                # for p in i.comment_id:
                #         comment = p.comments
                
                total_seconds = manual_time*60*60
                
                
                cummulative = total_seconds + total_second
                cummulative_time =  str(timedelta(seconds=cummulative))
                
                timed_time_for_day = timedelta(seconds=total_second)
                print "\n\n_________timed_time_for_day______________",timed_time_for_day,type(timed_time_for_day)
                # if total_second > 0.0:
                #         if total_seconds > 0.0:
                #                 if total_second > total_seconds :
                #                         timed_time = total_second - total_seconds
                #                 else:
                #                         timed_time = total_seconds - total_second
                # 
                # timed_time_for_day =  str(timedelta(seconds=timed_time))
               
                sr_no=sr_no+1
                    
                worksheet.write(row+3,col,sr_no,data_format)
                # col += 1
                
                worksheet.write(row+3,col+1,task_priority,data_format)
                # col += 1
                worksheet.write(row+3,col+2,task_type,data_format)
                # col += 1
                worksheet.write(row+3,col+3,task_name,data_format)
                # col += 1
                worksheet.write(row+3,col+4,start_format,data_format)
                # col += 1
                worksheet.write(row+3,col+5,stop_format,data_format)
                # col += 1
                worksheet.write(row+3,col+6,task_status,data_format)
                # col += 1
                worksheet.write(row+3,col+7,deadline,data_format)
                # col += 1
                if i.task_allocated_time :
                    alloted_time1 = datetime.strptime(alloted_time,'%H:%M:%S')
                    alloted_time2 = date.strftime(alloted_time1, '%H:%M')
                    worksheet.write(row+3,col+8,alloted_time2,data_format)
                # col += 1
                
                # col += 1

                timed_time_for_day_hr = timed_time_for_day.days * 24
                timed_time_for_day_min = timed_time_for_day.seconds//3600
                timed_time_for_day_sec = timed_time_for_day.seconds // 60 % 60
                if timed_time_for_day_sec < 10:
                    timed_time_for_day1 = str(timed_time_for_day_hr + timed_time_for_day_min) + ":"+"0" + str(timed_time_for_day_sec)
                else:
                    timed_time_for_day1 = str(timed_time_for_day_hr + timed_time_for_day_min) + ":" + str(timed_time_for_day_sec)
                print "\n\n______timed_time_for_day1________",timed_time_for_day1
                worksheet.write(row+3,col+10,timed_time_for_day1,data_format)
                # col += 1
                manual_time = str(timedelta(seconds=total_seconds))
                manual_time_delta= timedelta(seconds=total_seconds)
                manual_time1 = datetime.strptime(manual_time, '%H:%M:%S')
                manual_time2 = date.strftime(manual_time1, '%H:%M')
                worksheet.write(row+3,col+11,manual_time2,data_format)
                # col += 1

                date1 = datetime.strptime(start_format, '%Y-%m-%d')
                date1 = date.strftime(date1, '%Y-%m-%d')
                date2 = datetime.today()
                date2 = date.strftime(date2, '%Y-%m-%d')
                time_zero = datetime.strptime("00:00", '%H:%M') 
                cummulative_time1 = float(time_spent) + float(manual_time_delta.total_seconds())
                cummulative_time2 = timedelta(seconds=cummulative_time1)

                cummulative_time2_hr = cummulative_time2.days * 24
                cummulative_time2_min = cummulative_time2.seconds//3600
                cummulative_time2_sec = cummulative_time2.seconds // 60 % 60
                if cummulative_time2_sec < 10:
                    cummulative_time3 = str(cummulative_time2_hr + cummulative_time2_min) + ":"+"0" + str(cummulative_time2_sec)
                else:
                    cummulative_time3 = str(cummulative_time2_hr + cummulative_time2_min) + ":" + str(cummulative_time2_sec)
                worksheet.write(row+3,col+9,cummulative_time3,data_format)
                # x_timed_time = datetime.strptime(timed_time_for_day2, '%H:%M')
                # x_manual_time = datetime.strptime(manual_time2, '%H:%M')
                # if x_manual_time > x_timed_time:
                #     overlap_time = x_manual_time - x_timed_time
                # elif x_timed_time > x_manual_time:
                #     overlap_time = x_timed_time - x_manual_time
                # overlap_time =  str(timedelta(seconds=overlap_time))
                # overlap_time1 = datetime.strptime(str(overlap_time), '%H:%M:%S')
                # overlap_time2 = date.strftime(overlap_time1, '%H:%M')
                worksheet.write(row+3,col+12,str(overlap_time1),data_format)
                # col += 1
                
                worksheet.write(row+3,col+13,delay,data_format)
                # /col += 1
                if i.delay:
                    print "\n\n________REASON_________",i.task_delay_reason
                    worksheet.write(row+3,col+14,i.task_delay_reason,data_format)
                else:
                    worksheet.write(row+3,col+14,'No Delay',data_format)

                worksheet.write(row+3,col+15,all_comment,data_format)
                # col += 1
                row +=1
       
        
        title='Task Status wise report- Waiting for someone' 
        worksheet.write(row+4,col,title,header_format)
        worksheet.write(row+5,col,'S No',header_format)
        worksheet.write(row+5,col+1,'Task Priority',header_format)
        worksheet.write(row+5,col+2,'Task Type',header_format)
        worksheet.write(row+5,col+3,'Task Name',header_format)
        worksheet.write(row+5,col+4,'Start Date',header_format)
        worksheet.write(row+5,col+5,'End Date',header_format)
        worksheet.write(row+5,col+6,'Task Status',header_format)
        worksheet.write(row+5,col+7,'Deadline',header_format)
        worksheet.write(row+5,col+8,'Allotted Time  for the day',header_format)
        worksheet.write(row+5,col+9,'Cummulative Time',header_format)
        worksheet.write(row+5,col+10,'Timed Time for day',header_format)
        worksheet.write(row+5,col+11,'Manual Time for the day',header_format)
        worksheet.write(row+5,col+12,'Overlap Time for the day',header_format)
        worksheet.write(row+5,col+13,'Delay',header_format)
        worksheet.write(row+5,col+14,'Reason for Delay',header_format)
        worksheet.write(row+5,col+15,'Comments',header_format)
         
        
        
        task_search_ids = self.env['task.management'].search([('estimated_start_date','>=',self.date_from),('estimated_start_date','<=',self.date_to)
            ,('assigned_to','=',self.employee_id.id),('state','in',['waiting'])])
        
        row= row + 1
        sr_no = 0

        
        for i in task_search_ids:
                temp_count = 0
                col=0
                temp_row = 0
                total_second  = 0.0
                for l in i.task_history :
                        
                        date1 = l.task_history_date
                        date2 = datetime.today().strftime('%Y-%m-%d')

                        if date1 == date2 :       
                            total_second +=l.task_spend_time
                        
                overlap_time = 0.0
                overlap_time1 =0.0
                overlap_time_delta = timedelta(minutes=0)
                overlap_total = timedelta(minutes=0)
                comment  = []
                all_comment = ''
                a=[]
                for j in i.task_manual_time:
                    for l in i.task_history :
                        date1 = l.task_history_date
                        date2 = datetime.today().strftime('%Y-%m-%d')
                        date3 = j.task_manual_date
                        if date1 == date2:
                        
                            start = l.task_start_time
                            stop = l.task_stop_time
                            start1 = j.task_start_time
                            # start2 = datetime.strptime(str(start1), '%H.%M')
                            stop1 = j.task_end_time
                            # stop2 = datetime.strptime(str(stop1), '%H.%M')
                            # print "\n\n____stop2_____--",stop2
                            Range = namedtuple('Range', ['start', 'end'])
                            r1 = Range(start=start, end=stop)
                            r2 = Range(start=start1, end=stop1)
                            latest_start = max(r1.start, r2.start)
                            earliest_end = min(r1.end, r2.end)
                            if r1.start <= r2.start and r1.end >= r2.start or r1.start <= r2.end and r1.end >= r2.end:
                                delta = abs(latest_start - earliest_end)
                                delta = delta*60
                                overlap_time = str(timedelta(minutes=delta)).rsplit(':', 1)[0]
                                overlap_time_delta = timedelta(minutes=delta)
                                overlap_total += overlap_time_delta
                                # comment.append(str(j.task_manual_comments))
                                # all_comment = list(set(comment))
                                # all_comment = ', '.join(all_comment)
                            
                            if r1.start >= r2.start and r1.end <= r2.start or r1.start >= r2.end and r1.end <= r2.end:
                                delta = abs(latest_start - earliest_end)
                                delta = delta*60
                                overlap_time = str(timedelta(minutes=delta)).rsplit(':', 1)[0]
                                overlap_time_delta = timedelta(minutes=delta)
                                overlap_total += overlap_time_delta
                                # comment.append(str(j.task_manual_comments))
                                # all_comment = list(set(comment))
                                # all_comment = ', '.join(all_comment)

                    comment.append(str(j.task_manual_comments if j.task_manual_comments else ''))
                    all_comment = list(set(comment))
                    all_comment = ', '.join(all_comment)

                time_spent = i.x_time_spent  
                # comment.append(str(j.task_manual_comments))
                # all_comment = list(set(comment))
                # all_comment = ', '.join(all_comment)                   
                # if i.time_spent:
                #     time_spent = datetime.strptime(str(i.time_spent), '%H:%M')
                # else:
                #     time_spent = datetime.strptime(str("00:00"), '%H:%M')
                if overlap_time == 0.0:                    
                    overlap_time1 = date.strftime(datetime.strptime(str(overlap_total), '%H:%M:%S'), '%H:%M')
                else:
                    overlap_time1 = date.strftime(datetime.strptime(str(overlap_total), '%H:%M:%S'), '%H:%M')
                task_priority = dict(i._fields['task_priority'].selection).get(i.task_priority)
                task_type = dict(i._fields['task_type'].selection).get(i.task_type)
                task_status = dict(i._fields['state'].selection).get(i.state)
                task_name = i.name if i.name else " "
                start_date = i.estimated_start_date
                end_date = i.estimated_end_date
                user_pool = self.env['res.users']
                user_brws = user_pool.browse(SUPERUSER_ID)
                
                start_tz = pytz.utc.localize(parse(start_date))
                
                start_format = start_tz.strftime ("%Y-%m-%d")
                stop_tz = pytz.utc.localize(parse(end_date))
                
                stop_format = stop_tz.strftime ("%Y-%m-%d")
               
                # task_status = i.state
                deadline = i.deadline
                alloted_time = 0.0
                if i.task_allocated_time : 
                        alloted_time = i.task_allocated_time*3600
                        alloted_time = str(timedelta(seconds=alloted_time))
                
                myDate = date.today()    
                dateStr = str(myDate.year) +"-" + str(myDate.month)+ "-" + str(myDate.day)
                
                start_date = datetime.strptime(dateStr,'%Y-%m-%d')
                delay = 0
                if i.deadline:
                    end_date = datetime.strptime(i.deadline,'%Y-%m-%d')
                    diff = ''
                    if end_date < start_date:
                       diff = start_date - end_date
                       delay = diff.days
                
                manual_time = 0.0
                total_seconds = 0.0
                for j in i.task_manual_time:
                        
                    date1 = j.task_manual_date
                    date2 = datetime.today().strftime('%Y-%m-%d')
                    if date1 == date2 :
                        manual_time += j.task_manual_time
                        
                # for p in i.comment_id:
                #         comment = p.comments
                
                
                total_seconds = manual_time*60*60
                
                
                cummulative = total_seconds + total_second
                cummulative_time =  str(timedelta(seconds=cummulative))
                timed_time_for_day = timedelta(seconds=total_second)
                
                
                
                
                sr_no=sr_no+1
                    
                worksheet.write(row+5,col,sr_no,data_format)
                # col += 1
                
                worksheet.write(row+5,col+1,task_priority,data_format)
                # col += 1
                worksheet.write(row+5,col+2,task_type,data_format)
                # col += 1
                worksheet.write(row+5,col+3,task_name,data_format)
                # col += 1
                worksheet.write(row+5,col+4,start_format,data_format)
                # col += 1
                worksheet.write(row+5,col+5,stop_format,data_format)
                # col += 1
                worksheet.write(row+5,col+6,task_status,data_format)
                # col += 1
                worksheet.write(row+5,col+7,deadline,data_format)
                # col += 1
                if i.task_allocated_time :
                    alloted_time1 = datetime.strptime(alloted_time,'%H:%M:%S')
                    alloted_time2 = date.strftime(alloted_time1, '%H:%M')
                    worksheet.write(row+5,col+8,alloted_time2,data_format)
                # col += 1
                
                # col += 1
                
                timed_time_for_day_hr = timed_time_for_day.days * 24
                timed_time_for_day_min = timed_time_for_day.seconds//3600
                timed_time_for_day_sec = timed_time_for_day.seconds // 60 % 60
                if timed_time_for_day_sec < 10:
                    timed_time_for_day1 = str(timed_time_for_day_hr + timed_time_for_day_min) + ":"+"0" + str(timed_time_for_day_sec)
                else:
                    timed_time_for_day1 = str(timed_time_for_day_hr + timed_time_for_day_min) + ":" + str(timed_time_for_day_sec)
                print "\n\n______timed_time_for_day1________",timed_time_for_day1
                worksheet.write(row+5,col+10,timed_time_for_day1,data_format)
                # col += 1
                manual_time = str(timedelta(seconds=total_seconds))
                manual_time_delta= timedelta(seconds=total_seconds)
                manual_time1 = datetime.strptime(manual_time, '%H:%M:%S')
                manual_time2 = date.strftime(manual_time1, '%H:%M')
                worksheet.write(row+5,col+11,manual_time2,data_format)

                date1 = datetime.strptime(start_format, '%Y-%m-%d')
                date1 = date.strftime(date1, '%Y-%m-%d')
                date2 = datetime.today()
                date2 = date.strftime(date2, '%Y-%m-%d')
                time_zero = datetime.strptime("00:00", '%H:%M') 
                cummulative_time1 = float(time_spent) + float(manual_time_delta.total_seconds())
                cummulative_time2 = timedelta(seconds=cummulative_time1)

                cummulative_time2_hr = cummulative_time2.days * 24
                cummulative_time2_min = cummulative_time2.seconds//3600
                cummulative_time2_sec = cummulative_time2.seconds // 60 % 60
                if cummulative_time2_sec < 10:
                    cummulative_time3 = str(cummulative_time2_hr + cummulative_time2_min) + ":"+"0" + str(cummulative_time2_sec)
                else:
                    cummulative_time3 = str(cummulative_time2_hr + cummulative_time2_min) + ":" + str(cummulative_time2_sec)
                worksheet.write(row+5,col+9,cummulative_time3,data_format)
                # col += 1
                
                worksheet.write(row+5,col+12,str(overlap_time1),data_format)
                # col += 1
                
                worksheet.write(row+5,col+13,delay,data_format)
                # /col += 1
                if i.delay:
                    print "\n\n________REASON_________",i.task_delay_reason
                    worksheet.write(row+5,col+14,i.task_delay_reason,data_format)
                else:
                    worksheet.write(row+5,col+14,'No Delay',data_format)
                worksheet.write(row+5,col+15,all_comment,data_format)
                # col += 1
                row +=1
         
                
        title='Task Status wise report- Pause' 
        worksheet.write(row+6,col,title,header_format)
        worksheet.write(row+7,col,'S No',header_format)
        worksheet.write(row+7,col+1,'Task Priority',header_format)
        worksheet.write(row+7,col+2,'Task Type',header_format)
        worksheet.write(row+7,col+3,'Task Name',header_format)
        worksheet.write(row+7,col+4,'Start Date',header_format)
        worksheet.write(row+7,col+5,'End Date',header_format)
        worksheet.write(row+7,col+6,'Task Status',header_format)
        worksheet.write(row+7,col+7,'Deadline',header_format)
        worksheet.write(row+7,col+8,'Allotted Time  for the day',header_format)
        worksheet.write(row+7,col+9,'Cummulative Time',header_format)
        worksheet.write(row+7,col+10,'Timed Time for day',header_format)
        worksheet.write(row+7,col+11,'Manual Time for the day',header_format)
       
        worksheet.write(row+7,col+12,'Delay',header_format)
        worksheet.write(row+7,col+13,'Reason for Delay',header_format)
        worksheet.write(row+7,col+14,'Comments',header_format) 
        
       
        
        
        
        task_search_ids = self.env['task.management'].search([('estimated_start_date','>=',self.date_from),('estimated_start_date','<=',self.date_to)
            ,('assigned_to','=',self.employee_id.id),('state','in',['pause'])])
        
        
        row= row + 1
        sr_no = 0
        
        for i in task_search_ids:
                temp_count = 0
                col=0
                temp_row = 0
                total_second = 0.0
                for l in i.task_history :
                        # total_second = 0.0
                        date1 = l.task_history_date
                        date2 = datetime.today().strftime('%Y-%m-%d')
                        # if date1 == date2 :
                        total_second += l.task_spend_time
                            
                overlap_time = 0.0
                overlap_time1 =0.0
                overlap_time_delta = timedelta(minutes=0)
                overlap_total = timedelta(minutes=0)
                comment  = []
                all_comment = ''
                a=[]
                for j in i.task_manual_time:
                    for l in i.task_history :
                        date1 = l.task_history_date
                        date2 = datetime.today().strftime('%Y-%m-%d')
                        date3 = j.task_manual_date
                        if date1 == date2:
                        
                            start = l.task_start_time
                            stop = l.task_stop_time
                            start1 = j.task_start_time
                            # start2 = datetime.strptime(str(start1), '%H.%M')
                            stop1 = j.task_end_time
                            # stop2 = datetime.strptime(str(stop1), '%H.%M')
                            # print "\n\n____stop2_____--",stop2
                            Range = namedtuple('Range', ['start', 'end'])
                            r1 = Range(start=start, end=stop)
                            r2 = Range(start=start1, end=stop1)
                            latest_start = max(r1.start, r2.start)
                            earliest_end = min(r1.end, r2.end)
                            if r1.start <= r2.start and r1.end >= r2.start or r1.start <= r2.end and r1.end >= r2.end:
                                delta = abs(latest_start - earliest_end)
                                delta = delta*60
                                overlap_time = str(timedelta(minutes=delta)).rsplit(':', 1)[0]
                                overlap_time_delta = timedelta(minutes=delta)
                                overlap_total += overlap_time_delta
                                # comment.append(str(j.task_manual_comments))
                                # all_comment = list(set(comment))
                                # all_comment = ', '.join(all_comment)
                            
                            if r1.start >= r2.start and r1.end <= r2.start or r1.start >= r2.end and r1.end <= r2.end:
                                delta = abs(latest_start - earliest_end)
                                delta = delta*60
                                overlap_time = str(timedelta(minutes=delta)).rsplit(':', 1)[0]
                                overlap_time_delta = timedelta(minutes=delta)
                                overlap_total += overlap_time_delta
                                # comment.append(str(j.task_manual_comments))
                                # all_comment = list(set(comment))
                                # all_comment = ', '.join(all_comment)

                    comment.append(str(j.task_manual_comments if j.task_manual_comments else ''))
                    all_comment = list(set(comment))
                    all_comment = ', '.join(all_comment)

                time_spent = i.x_time_spent
                
                # if i.time_spent:
                #     time_spent = datetime.strptime(str(i.time_spent), '%H:%M')
                # else:
                #     time_spent = datetime.strptime(str("00:00"), '%H:%M')
                if overlap_time == 0.0:                    
                    overlap_time1 = date.strftime(datetime.strptime(str(overlap_total), '%H:%M:%S'), '%H:%M')
                else:
                    overlap_time1 = date.strftime(datetime.strptime(str(overlap_total), '%H:%M:%S'), '%H:%M')
                                     
                task_priority = dict(i._fields['task_priority'].selection).get(i.task_priority)
                task_type = dict(i._fields['task_type'].selection).get(i.task_type)
                task_status = dict(i._fields['state'].selection).get(i.state)
                task_name = i.name if i.name else " "
                start_date = i.estimated_start_date
                end_date = i.estimated_end_date
                user_pool = self.env['res.users']
                user_brws = user_pool.browse(SUPERUSER_ID)
                
                start_tz = pytz.utc.localize(parse(start_date))
                
                start_format = start_tz.strftime ("%Y-%m-%d")
                stop_tz = pytz.utc.localize(parse(end_date))
                
                stop_format = stop_tz.strftime ("%Y-%m-%d")
               
                # task_status = i.state
                deadline = i.deadline
                alloted_time = 0.0
                if i.task_allocated_time : 
                        alloted_time = i.task_allocated_time*3600
                        alloted_time = str(timedelta(seconds=alloted_time))
                
                myDate = date.today()    
                dateStr = str(myDate.year) +"-" + str(myDate.month)+ "-" + str(myDate.day)
                
                start_date = datetime.strptime(dateStr,'%Y-%m-%d')
                
                delay = 0
                if i.deadline:
                    end_date = datetime.strptime(i.deadline,'%Y-%m-%d')
                    diff = ''
                    if end_date < start_date:
                       diff = start_date - end_date
                       delay = diff.days
                
                manual_time = 0.0
                total_seconds = 0.0
                for j in i.task_manual_time:
                        
                    date1 = j.task_manual_date
                    date2 = datetime.today().strftime('%Y-%m-%d')
                    if date1 == date2 :
                        manual_time += j.task_manual_time
                        
                # for p in i.comment_id:
                #         comment = p.comments
                
                
                total_seconds = manual_time*60*60
                
                
                cummulative = total_seconds + total_second
                cummulative_time =  str(timedelta(seconds=cummulative))
                timed_time_for_day = timedelta(seconds=total_second)
                
                
                
                sr_no=sr_no+1
                    
                worksheet.write(row+7,col,sr_no,data_format)
                # col += 1
                
                worksheet.write(row+7,col+1,task_priority,data_format)
                # col += 1
                worksheet.write(row+7,col+2,task_type,data_format)
                # col += 1
                worksheet.write(row+7,col+3,task_name,data_format)
                # col += 1
                worksheet.write(row+7,col+4,start_format,data_format)
                # col += 1
                worksheet.write(row+7,col+5,stop_format,data_format)
                # col += 1
                worksheet.write(row+7,col+6,task_status,data_format)
                # col += 1
                worksheet.write(row+7,col+7,deadline,data_format)
                # col += 1
                if i.task_allocated_time :
                    alloted_time1 = datetime.strptime(alloted_time,'%H:%M:%S')
                    alloted_time2 = date.strftime(alloted_time1, '%H:%M')
                    worksheet.write(row+7,col+8,alloted_time2,data_format)
                # col += 1
                
                # col += 1
                timed_time_for_day_hr = timed_time_for_day.days * 24
                timed_time_for_day_min = timed_time_for_day.seconds//3600
                timed_time_for_day_sec = timed_time_for_day.seconds // 60 % 60
                if timed_time_for_day_sec < 10:
                    timed_time_for_day1 = str(timed_time_for_day_hr + timed_time_for_day_min) + ":"+"0" + str(timed_time_for_day_sec)
                else:
                    timed_time_for_day1 = str(timed_time_for_day_hr + timed_time_for_day_min) + ":" + str(timed_time_for_day_sec)
                print "\n\n______timed_time_for_day1________",timed_time_for_day1
                worksheet.write(row+7,col+10,timed_time_for_day1,data_format)
                # col += 1
                manual_time = str(timedelta(seconds=total_seconds))
                manual_time_delta= timedelta(seconds=total_seconds)
                manual_time1 = datetime.strptime(manual_time, '%H:%M:%S')
                manual_time2 = date.strftime(manual_time1, '%H:%M')
                worksheet.write(row+7,col+11,manual_time2,data_format)
                # col += 1
                date1 = datetime.strptime(start_format, '%Y-%m-%d')
                date1 = date.strftime(date1, '%Y-%m-%d')
                date2 = datetime.today()
                date2 = date.strftime(date2, '%Y-%m-%d')
                time_zero = datetime.strptime("00:00", '%H:%M') 
                cummulative_time1 = float(time_spent) + float(manual_time_delta.total_seconds())
                cummulative_time2 = timedelta(seconds=cummulative_time1)

                cummulative_time2_hr = cummulative_time2.days * 24
                cummulative_time2_min = cummulative_time2.seconds//3600
                cummulative_time2_sec = cummulative_time2.seconds // 60 % 60
                if cummulative_time2_sec < 10:
                    cummulative_time3 = str(cummulative_time2_hr + cummulative_time2_min) + ":"+"0" + str(cummulative_time2_sec)
                else:
                    cummulative_time3 = str(cummulative_time2_hr + cummulative_time2_min) + ":" + str(cummulative_time2_sec)
                worksheet.write(row+7,col+9,cummulative_time3,data_format)
                # worksheet.write(row+5,col+12,overlap_time,data_format)
                # col += 1
                
                worksheet.write(row+7,col+12,delay,data_format)
                # /col += 1
                if i.delay:
                    print "\n\n________REASON_________",i.task_delay_reason
                    worksheet.write(row+7,col+13,i.task_delay_reason,data_format)
                else:
                    worksheet.write(row+7,col+13,'No Delay',data_format)
                worksheet.write(row+7,col+14,all_comment,data_format)
                # col += 1
                row +=1
        
        
        
        title='Task Status wise report- Drop' 
        worksheet.write(row+8,col,title,header_format)
        worksheet.write(row+9,col,'S No',header_format)
        worksheet.write(row+9,col+1,'Task Priority',header_format)
        worksheet.write(row+9,col+2,'Task Type',header_format)
        worksheet.write(row+9,col+3,'Task Name',header_format)
        worksheet.write(row+9,col+4,'Start Date',header_format)
        worksheet.write(row+9,col+5,'End Date',header_format)
        worksheet.write(row+9,col+6,'Task Status',header_format)
        worksheet.write(row+9,col+7,'Deadline',header_format)
        worksheet.write(row+9,col+8,'Allotted Time  for the day',header_format)
        worksheet.write(row+9,col+9,'Cummulative Time',header_format)
        worksheet.write(row+9,col+10,'Timed Time for day',header_format)
        worksheet.write(row+9,col+11,'Manual Time for the day',header_format)
       
        worksheet.write(row+9,col+12,'Delay',header_format)
        worksheet.write(row+9,col+13,'Reason for Delay',header_format)
        worksheet.write(row+9,col+14,'Comments',header_format) 
        
        task_search_ids = self.env['task.management'].search([('estimated_start_date','>=',self.date_from),('estimated_start_date','<=',self.date_to)
            ,('assigned_to','=',self.employee_id.id),('state','in',['drop'])])
        
        row= row + 1
        sr_no = 0
        
        for i in task_search_ids:
                temp_count = 0
                col=0
                temp_row = 0
                total_second = 0.0
                for l in i.task_history :
                       
                        date1 = l.task_history_date
                        date2 = datetime.today().strftime('%Y-%m-%d')
                        # if date1 == date2 :
                                
                        total_second +=l.task_spend_time
                        
                overlap_time = 0.0
                overlap_time1 =0.0
                overlap_time_delta = timedelta(minutes=0)
                overlap_total = timedelta(minutes=0)
                comment  = []
                all_comment = ''
                a=[]
                for j in i.task_manual_time:
                    for l in i.task_history :
                        date1 = l.task_history_date
                        date2 = datetime.today().strftime('%Y-%m-%d')
                        date3 = j.task_manual_date
                        if date1 == date2:
                        
                            start = l.task_start_time
                            stop = l.task_stop_time
                            start1 = j.task_start_time
                            # start2 = datetime.strptime(str(start1), '%H.%M')
                            stop1 = j.task_end_time
                            # stop2 = datetime.strptime(str(stop1), '%H.%M')
                            # print "\n\n____stop2_____--",stop2
                            Range = namedtuple('Range', ['start', 'end'])
                            r1 = Range(start=start, end=stop)
                            r2 = Range(start=start1, end=stop1)
                            latest_start = max(r1.start, r2.start)
                            earliest_end = min(r1.end, r2.end)
                            if r1.start <= r2.start and r1.end >= r2.start or r1.start <= r2.end and r1.end >= r2.end:
                                delta = abs(latest_start - earliest_end)
                                delta = delta*60
                                overlap_time = str(timedelta(minutes=delta)).rsplit(':', 1)[0]
                                overlap_time_delta = timedelta(minutes=delta)
                                overlap_total += overlap_time_delta
                                # comment.append(str(j.task_manual_comments))
                                # all_comment = list(set(comment))
                                # all_comment = ', '.join(all_comment)
                            
                            if r1.start >= r2.start and r1.end <= r2.start or r1.start >= r2.end and r1.end <= r2.end:
                                delta = abs(latest_start - earliest_end)
                                delta = delta*60
                                overlap_time = str(timedelta(minutes=delta)).rsplit(':', 1)[0]
                                overlap_time_delta = timedelta(minutes=delta)
                                overlap_total += overlap_time_delta
                                # comment.append(str(j.task_manual_comments))
                                # all_comment = list(set(comment))
                                # all_comment = ', '.join(all_comment)

                    comment.append(str(j.task_manual_comments if j.task_manual_comments else ''))
                    all_comment = list(set(comment))
                    all_comment = ', '.join(all_comment)
                
                time_spent = i.x_time_spent 
                               
                # if i.time_spent:
                #     time_spent = datetime.strptime(str(i.time_spent), '%H:%M')
                # else:
                #     time_spent = datetime.strptime(str("00:00"), '%H:%M')
                if overlap_time == 0.0:                    
                    overlap_time1 = date.strftime(datetime.strptime(str(overlap_total), '%H:%M:%S'), '%H:%M')
                else:
                    overlap_time1 = date.strftime(datetime.strptime(str(overlap_total), '%H:%M:%S'), '%H:%M')                    
                task_priority = dict(i._fields['task_priority'].selection).get(i.task_priority)
                task_type = dict(i._fields['task_type'].selection).get(i.task_type)
                task_status = dict(i._fields['state'].selection).get(i.state)
                task_name = i.name if i.name else " "
                start_date = i.estimated_start_date
                end_date = i.estimated_end_date
                user_pool = self.env['res.users']
                user_brws = user_pool.browse(SUPERUSER_ID)
                
                start_tz = pytz.utc.localize(parse(start_date))
                
                start_format = start_tz.strftime ("%Y-%m-%d")
                stop_tz = pytz.utc.localize(parse(end_date))
                
                stop_format = stop_tz.strftime ("%Y-%m-%d")
               
                deadline = i.deadline
                alloted_time = 0.0
                if i.task_allocated_time : 
                        alloted_time = i.task_allocated_time*3600
                        alloted_time = str(timedelta(seconds=alloted_time))
                
                myDate = date.today()    
                dateStr = str(myDate.year) +"-" + str(myDate.month)+ "-" + str(myDate.day)
                
                start_date = datetime.strptime(dateStr,'%Y-%m-%d')
                delay = 0
                if i.deadline:
                    end_date = datetime.strptime(i.deadline,'%Y-%m-%d')
                    diff = ''
                    if end_date < start_date:
                       diff = start_date - end_date
                       delay = diff.days
                
                manual_time = 0.0
                total_seconds = 0.0

                for j in i.task_manual_time:
                        
                    date1 = j.task_manual_date
                    date2 = datetime.today().strftime('%Y-%m-%d')
                    if date1 == date2 :
                        manual_time += j.task_manual_time
                    
                        
                # for p in i.comment_id:
                #         comment = p.comments
                        
                
                
                total_seconds = manual_time*60*60
                
                
                cummulative = total_seconds + total_second
                cummulative_time =  str(timedelta(seconds=cummulative))
                timed_time_for_day = timedelta(seconds=total_second)
                
               

                # comment = i.observer_comments if i.observer_comments else "NA"
                
               
                sr_no=sr_no+1
                    
                worksheet.write(row+9,col,sr_no,data_format)
                # col += 1
                
                worksheet.write(row+9,col+1,task_priority,data_format)
                # col += 1
                worksheet.write(row+9,col+2,task_type,data_format)
                # col += 1
                worksheet.write(row+9,col+3,task_name,data_format)
                # col += 1
                worksheet.write(row+9,col+4,start_format,data_format)
                # col += 1
                worksheet.write(row+9,col+5,stop_format,data_format)
                # col += 1
                worksheet.write(row+9,col+6,task_status,data_format)
                # col += 1
                worksheet.write(row+9,col+7,deadline,data_format)
                # col += 1
                if i.task_allocated_time :
                    alloted_time1 = datetime.strptime(alloted_time,'%H:%M:%S')
                    alloted_time2 = date.strftime(alloted_time1, '%H:%M')
                    worksheet.write(row+9,col+8,alloted_time2,data_format)
                # col += 1
                
                # col += 1
                
                timed_time_for_day1 = datetime.strptime(timed_time_for_day, '%H:%M')
                timed_time_for_day2 = date.strftime(timed_time_for_day1, '%H:%M')
                worksheet.write(row+9,col+10,timed_time_for_day2,data_format)
                # col += 1
                date1 = datetime.strptime(start_format, '%Y-%m-%d')
                date1 = date.strftime(date1, '%Y-%m-%d')
                date2 = datetime.today()
                date2 = date.strftime(date2, '%Y-%m-%d')
                time_zero = datetime.strptime("00:00", '%H:%M') 
                cummulative_time1 = float(time_spent) + float(manual_time_delta.total_seconds())
                cummulative_time2 = timedelta(seconds=cummulative_time1)

                cummulative_time2_hr = cummulative_time2.days * 24
                cummulative_time2_min = cummulative_time2.seconds//3600
                cummulative_time2_sec = cummulative_time2.seconds // 60 % 60
                if cummulative_time2_sec < 10:
                    cummulative_time3 = str(cummulative_time2_hr + cummulative_time2_min) + ":"+"0" + str(cummulative_time2_sec)
                else:
                    cummulative_time3 = str(cummulative_time2_hr + cummulative_time2_min) + ":" + str(cummulative_time2_sec)
                worksheet.write(row+9,col+9,cummulative_time3,data_format)
                # worksheet.write(row+5,col+12,overlap_time,data_format)
                # col += 1
                
                worksheet.write(row+9,col+12,delay,data_format)
                # /col += 1
                if i.delay:
                    print "\n\n________REASON_________",i.task_delay_reason
                    worksheet.write(row+9,col+13,i.task_delay_reason,data_format)
                else:
                    worksheet.write(row+9,col+13,'No Delay',data_format)
                worksheet.write(row+9,col+14,all_comment,data_format)
                # col += 1
                row +=1
                
        
        title='Task Status wise report- Completed' 
        worksheet.write(row+10,col,title,header_format)
        worksheet.write(row+11,col,'S No',header_format)
        worksheet.write(row+11,col+1,'Task Priority',header_format)
        worksheet.write(row+11,col+2,'Task Type',header_format)
        worksheet.write(row+11,col+3,'Task Name',header_format)
        worksheet.write(row+11,col+4,'Start Date',header_format)
        worksheet.write(row+11,col+5,'End Date',header_format)
        worksheet.write(row+11,col+6,'Task Status',header_format)
        worksheet.write(row+11,col+7,'Deadline',header_format)
        worksheet.write(row+11,col+8,'Allotted Time  for the day',header_format)
        worksheet.write(row+11,col+9,'Cummulative Time',header_format)
        worksheet.write(row+11,col+10,'Timed Time for day',header_format)
        worksheet.write(row+11,col+11,'Manual Time for the day',header_format)
        worksheet.write(row+11,col+12,'% of Completion',header_format)
        worksheet.write(row+11,col+13,'Delay',header_format)
        worksheet.write(row+11,col+14,'Reason for Delay',header_format)
        worksheet.write(row+11,col+15,'Comments',header_format)
        
       
        
        task_search_ids = self.env['task.management'].search([('estimated_start_date','>=',self.date_from),('estimated_start_date','<=',self.date_to)
            ,('assigned_to','=',self.employee_id.id),('state','in',['completed'])])
        
        row= row + 1
        sr_no = 0
        
        for i in task_search_ids:
                temp_count = 0
                col=0
                temp_row = 0
                total_second = 0.0
                for l in i.task_history :
                        date1 = l.task_history_date
                        date2 = datetime.today().strftime('%Y-%m-%d')
                        if date1 == date2 :       
                                total_second +=l.task_spend_time
                        
                overlap_time = 0.0
                overlap_time1 =0.0
                overlap_time_delta = timedelta(minutes=0)
                overlap_total = timedelta(minutes=0)
                comment  = []
                all_comment = ''
                a=[]
                for j in i.task_manual_time:
                    for l in i.task_history :
                        date1 = l.task_history_date
                        date2 = datetime.today().strftime('%Y-%m-%d')
                        date3 = j.task_manual_date
                        if date1 == date2:
                        
                            start = l.task_start_time
                            stop = l.task_stop_time
                            start1 = j.task_start_time
                            # start2 = datetime.strptime(str(start1), '%H.%M')
                            stop1 = j.task_end_time
                            # stop2 = datetime.strptime(str(stop1), '%H.%M')
                            # print "\n\n____stop2_____--",stop2
                            Range = namedtuple('Range', ['start', 'end'])
                            r1 = Range(start=start, end=stop)
                            r2 = Range(start=start1, end=stop1)
                            latest_start = max(r1.start, r2.start)
                            earliest_end = min(r1.end, r2.end)
                            if r1.start <= r2.start and r1.end >= r2.start or r1.start <= r2.end and r1.end >= r2.end:
                                delta = abs(latest_start - earliest_end)
                                delta = delta*60
                                overlap_time = str(timedelta(minutes=delta)).rsplit(':', 1)[0]
                                overlap_time_delta = timedelta(minutes=delta)
                                overlap_total += overlap_time_delta
                                # comment.append(str(j.task_manual_comments))
                                # all_comment = list(set(comment))
                                # all_comment = ', '.join(all_comment)
                            
                            if r1.start >= r2.start and r1.end <= r2.start or r1.start >= r2.end and r1.end <= r2.end:
                                delta = abs(latest_start - earliest_end)
                                delta = delta*60
                                overlap_time = str(timedelta(minutes=delta)).rsplit(':', 1)[0]
                                overlap_time_delta = timedelta(minutes=delta)
                                overlap_total += overlap_time_delta
                                # comment.append(str(j.task_manual_comments))
                                # all_comment = list(set(comment))
                                # all_comment = ', '.join(all_comment)

                    comment.append(str(j.task_manual_comments if j.task_manual_comments else ''))
                    all_comment = list(set(comment))
                    all_comment = ', '.join(all_comment)
                
                time_spent = i.x_time_spent
                
                # if i.time_spent:
                #     time_spent = datetime.strptime(str(i.time_spent), '%H:%M')
                # else:
                #     time_spent = datetime.strptime(str("00:00"), '%H:%M')
                if overlap_time == 0.0:                    
                    overlap_time1 = date.strftime(datetime.strptime(str(overlap_total), '%H:%M:%S'), '%H:%M')
                else:
                    overlap_time1 = date.strftime(datetime.strptime(str(overlap_total), '%H:%M:%S'), '%H:%M')                    
                task_priority = dict(i._fields['task_priority'].selection).get(i.task_priority)
                task_type = dict(i._fields['task_type'].selection).get(i.task_type)
                task_status = dict(i._fields['state'].selection).get(i.state)
                task_name = i.name if i.name else " "
                start_date = i.estimated_start_date
                end_date = i.estimated_end_date
                user_pool = self.env['res.users']
                user_brws = user_pool.browse(SUPERUSER_ID)
                
                start_tz = pytz.utc.localize(parse(start_date))
                
                start_format = start_tz.strftime ("%Y-%m-%d")
                stop_tz = pytz.utc.localize(parse(end_date))
                
                stop_format = stop_tz.strftime ("%Y-%m-%d")
               
                # task_status = i.state
                deadline = i.deadline
                alloted_time = 0.0
                if i.task_allocated_time : 
                        alloted_time = i.task_allocated_time*3600
                        alloted_time = str(timedelta(seconds=alloted_time))
                
                myDate = date.today()    
                dateStr = str(myDate.year) +"-" + str(myDate.month)+ "-" + str(myDate.day)
                
                start_date = datetime.strptime(dateStr,'%Y-%m-%d')
                delay = 0
                if i.deadline:
                    end_date = datetime.strptime(i.deadline,'%Y-%m-%d')
                    diff = ''
                    if end_date < start_date:
                       diff = start_date - end_date
                       delay = diff.days
                
                manual_time = 0.0
                total_seconds = 0.0
                for j in i.task_manual_time:
                        
                    date1 = j.task_manual_date
                    date2 = datetime.today().strftime('%Y-%m-%d')
                    if date1 == date2 :
                        manual_time += j.task_manual_time
                        
                # for p in i.comment_id:
                #         comment = p.comments
                
                total_seconds = manual_time*60*60
                
                
                cummulative = total_seconds + total_second
                cummulative_time =  str(timedelta(seconds=cummulative))
                
                timed_time_for_day = timedelta(seconds=total_second)
               
                task_completion_per = i.percantage_task_completion    
                # comment = i.observer_comments if i.observer_comments else "NA"
                
               
                sr_no=sr_no+1
                    
                worksheet.write(row+11,col,sr_no,data_format)
                # col += 1
                
                worksheet.write(row+11,col+1,task_priority,data_format)
                # col += 1
                worksheet.write(row+11,col+2,task_type,data_format)
                # col += 1
                worksheet.write(row+11,col+3,task_name,data_format)
                # col += 1
                worksheet.write(row+11,col+4,start_format,data_format)
                # col += 1
                worksheet.write(row+11,col+5,stop_format,data_format)
                # col += 1
                worksheet.write(row+11,col+6,task_status,data_format)
                # col += 1
                worksheet.write(row+11,col+7,deadline,data_format)
                # col += 1
                if i.task_allocated_time :
                    alloted_time1 = datetime.strptime(alloted_time,'%H:%M:%S')
                    alloted_time2 = date.strftime(alloted_time1, '%H:%M')
                    worksheet.write(row+11,col+8,alloted_time2,data_format)
                # col += 1
                
                # col += 1
                
                timed_time_for_day_hr = timed_time_for_day.days * 24
                timed_time_for_day_min = timed_time_for_day.seconds//3600
                timed_time_for_day_sec = timed_time_for_day.seconds // 60 % 60
                if timed_time_for_day_sec < 10:
                    timed_time_for_day1 = str(timed_time_for_day_hr + timed_time_for_day_min) + ":"+"0" + str(timed_time_for_day_sec)
                else:
                    timed_time_for_day1 = str(timed_time_for_day_hr + timed_time_for_day_min) + ":" + str(timed_time_for_day_sec)
                print "\n\n______timed_time_for_day1________",timed_time_for_day1
                worksheet.write(row+11,col+10,timed_time_for_day1,data_format)
                # col += 1
                manual_time = str(timedelta(seconds=total_seconds))
                manual_time_delta= timedelta(seconds=total_seconds)
                manual_time1 = datetime.strptime(manual_time, '%H:%M:%S')
                manual_time2 = date.strftime(manual_time1, '%H:%M')
                worksheet.write(row+11,col+11,manual_time2,data_format)
                # col += 1
                date1 = datetime.strptime(start_format, '%Y-%m-%d')
                date1 = date.strftime(date1, '%Y-%m-%d')
                date2 = datetime.today()
                date2 = date.strftime(date2, '%Y-%m-%d')
                time_zero = datetime.strptime("00:00", '%H:%M') 
                cummulative_time1 = float(time_spent) + float(manual_time_delta.total_seconds())
                cummulative_time2 = timedelta(seconds=cummulative_time1)

                cummulative_time2_hr = cummulative_time2.days * 24
                cummulative_time2_min = cummulative_time2.seconds//3600
                cummulative_time2_sec = cummulative_time2.seconds // 60 % 60
                if cummulative_time2_sec < 10:
                    cummulative_time3 = str(cummulative_time2_hr + cummulative_time2_min) + ":"+"0" + str(cummulative_time2_sec)
                else:
                    cummulative_time3 = str(cummulative_time2_hr + cummulative_time2_min) + ":" + str(cummulative_time2_sec)
                worksheet.write(row+11,col+9,cummulative_time3,data_format)

                worksheet.write(row+11,col+12,task_completion_per,data_format)
                # col += 1
                
                worksheet.write(row+11,col+13,delay,data_format)
                # /col += 1
                if i.delay:
                    print "\n\n________REASON_________",i.task_delay_reason
                    worksheet.write(row+11,col+14,i.task_delay_reason,data_format)
                else:
                    worksheet.write(row+11,col+14,'No Delay',data_format)
                worksheet.write(row+11,col+15,all_comment,data_format)
                # col += 1
                row +=1
        
        
        
        
        
        
        workbook.close()
        out=base64.encodestring(fp.getvalue())
        data = (file_name,base64.b64decode(out))	
        cd=self.write({'excel_sheet':out, 'file_name':file_name})
        return True


    @api.multi
    def print_daily_report(self):
        for rec in self:
            date_from=rec.date_from
            date_to=rec.date_to
            # if date_from > date_to:
            #      raise ValidationError(_('Please Select Proper Date.'))                
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
        file_name = 'Task Daily Reports.xlsx'
        report_name = 'Task Daily Report'
        worksheet = workbook.add_worksheet(report_name)
        
        title='Daily Task Performed' 
        # date = datetime.now().strftime('%Y-%m-%d')
        worksheet.merge_range(0, 4, 0, 10,title,title_format)
        # worksheet.merge_range(0,10,0,12,date,title_format)
        worksheet.write('A2:A2','Sr. No.',header_format)
        worksheet.write('B2:B2','Task Priority',header_format)
        worksheet.write('C2:C2','Task Type',header_format)
        worksheet.write('D2:D2','Task Name',header_format)
        worksheet.write('E2:E2','Suggested Start Date',header_format)
        worksheet.write('F2:F2','End Date',header_format)
        worksheet.write('G2:G2','Task Status',header_format)
        # worksheet.write('H2:H2','Attended Time for the day',header_format)
        worksheet.write('H2:H2','Deadline',header_format)
        worksheet.write('I2:I2','Allocated Time',header_format)
        worksheet.write('J2:J2','Cummulative Time',header_format)
        worksheet.write('K2:K2','Timed Time for day',header_format)
        worksheet.write('L2:L2','Manual Time for the day',header_format)
        worksheet.write('M2:M2','Total Working Time for the day',header_format)
        worksheet.write('N2:N2','Overlap Time for the day',header_format)
        # worksheet.write('O2:O2','Idle Time for the day',header_format)
        worksheet.write('O2:O2','Initial % of Completion',header_format)
        worksheet.write('P2:P2','Current % of Completion',header_format)
        worksheet.write('Q2:Q2','% of Completion',header_format)
        worksheet.write('R2:R2','Variation',header_format)
        worksheet.write('S2:S2','Delay',header_format)
        worksheet.write('T2:T2','Reason for Delay',header_format)
        worksheet.write('U2:U2','Comments',header_format)
        
        
        myDate = date.today()
        today_date =  str(myDate.month)+ "/" + str(myDate.day) + "/" + str(myDate.year)
        todays_date = datetime.today().strftime('%Y-%m-%d')
        task_search_ids = self.env['task.management'].search([
                                            ('assigned_to','=',self.employee_id.id),
                                            ('state','in',['draft','drop','deffered','waiting','pause','completed','in_progress'])])
        print "\n\n_______task_search_ids_______",task_search_ids
        # ts_ids = self.env['task.management'].search([('current_date','=',todays_date),('assigned_to','=',self.employee_id.id)])
        # print "\n\n___________ts_ids______________",ts_ids
        # ('state','in',['draft','drop','deffered','waiting','pause','completed','in_progress'])])
        # task_summary_ids = self.env['task.summary'].search([('reviewer_id','=',self.reviewer_id1.id)])
        # print "\n\n______task_summary_ids_____1452____-",task_summary_ids

        rewer_id = task_search_ids[0].task_summary_id.reviewer_id
        print "\n\n________rewer_id_________",rewer_id,rewer_id.name
        if rewer_id:
            worksheet.merge_range(0, 14, 0, 18, "Reviewer: "+rewer_id.name,title_format)

        worksheet.merge_range(0,11,0,13,'Date: ' + todays_date,title_format)
        row=2
        sr_no = 0
        total_cummutative = timedelta(hours=0)
        total_active_time = 0.0
        total_overlap = 0.0
        gap = 0.0
        total_ovrlp = timedelta(hours=0)
        total_working = timedelta(hours=0)
        total_working1 = timedelta(hours=0)
        total_ideal_time = timedelta(hours=0)
        total_ideal_time1 = timedelta(hours=0)
        attended_time_delta = timedelta(hours=0)
        total_alloted = timedelta(hours=0)
        total_timed_time = timedelta(hours=0)
        total_manual = timedelta(hours=0)
        total_alloted1 = timedelta(minutes=0)
        total_manual1 = timedelta(minutes=0)
        total_timed_time1 = timedelta(minutes=0)
        total_cummutative1 = timedelta(minutes=0)

        
        for i in task_search_ids:
            temp_count = 0
            col=0
            temp_row = 0
            percent = 0.0
            
            print "\n\n_______i.time_spent______54____",i.time_spent
            employee = i.assigned_to.name
            worksheet.merge_range(0, 0, 0, 3, "Employee: "+employee,title_format)
            


            total_second = 0.0
            current_completion = 0.0
            current_progress = 0.0
            for l in i.task_history :
                    date1 = l.task_history_date
                    date2 = datetime.today().strftime('%Y-%m-%d')

                    print "\n\n______l.task_spend_time___58_____",l.task_spend_time
                    if date1 == date2:
                        total_second +=l.task_spend_time
                        print "\n\n______total_second____61_____",total_second

                        
                    print "\n\n___________i.current_completion___________",i.current_completion
                    if date1 < date2 or date1 == date2: 
                        print "\n\n_________inside iffffff_________" 
                        percent = 0.0 
                        percent = l.task_percent_completion 
                        i.initial_completion = l.task_percent_completion 
                        i.current_completion = i.percantage_task_completion 
                        current_completion = i.current_completion 
                    else: 
                        current_completion = 0.0

                    if date1 < date2 or date1 == date2:
                        per = 0.0
                        per = l.progress_percent
                        i.initial_progress = l.progress_percent
                        i.current_progress = i.progress
                        current_progress = i.current_progress
                    else:
                        current_progress = 0.0




            difference = 0.0
            if i.current_completion > 0.0:
                    difference = float(i.current_completion) - float(i.initial_completion)

            difference1 = 0.0
            if i.current_progress > 0.0:
                difference1 = float(i.current_progress) - float(i.initial_progress)

            print"\n\n____________i.initial_progress____1538____",i.initial_progress
            print "___________i.current_progress_____1539____",i.current_progress
            print "_________i.current_progress_______1540______-",difference1

            
            overlap_time = 0.0
            overlap_time1 =0.0
            overlap_time_delta = timedelta(minutes=0)
            overlap_total = timedelta(minutes=0)
            alloted_time_delta = timedelta(minutes=0)
            
            comment  = []    
            all_comment = ''        
            a=[]
            for j in i.task_manual_time:
                    for l in i.task_history :
                        date1 = l.task_history_date
                        date2 = datetime.today().strftime('%Y-%m-%d')
                        date3 = j.task_manual_date
                        if date1 == date2 and date1 == date3:
                        
                            start = l.task_start_time
                            stop = l.task_stop_time
                            start1 = j.task_start_time
                            # start2 = datetime.strptime(str(start1), '%H.%M')
                            stop1 = j.task_end_time
                            # stop2 = datetime.strptime(str(stop1), '%H.%M')
                            # print "\n\n____stop2_____--",stop2
                            Range = namedtuple('Range', ['start', 'end'])
                            r1 = Range(start=start, end=stop)
                            r2 = Range(start=start1, end=stop1)
                            latest_start = max(r1.start, r2.start)
                            earliest_end = min(r1.end, r2.end)
                            if r1.start <= r2.start and r1.end >= r2.start or r1.start <= r2.end and r1.end >= r2.end:
                                delta = abs(latest_start - earliest_end)
                                delta = delta*60
                                overlap_time = str(timedelta(minutes=delta)).rsplit(':', 1)[0]
                                overlap_time_delta = timedelta(minutes=delta)
                                overlap_total += overlap_time_delta
                                # comment.append(str(j.task_manual_comments))
                                # all_comment = list(set(comment))
                                # all_comment = ', '.join(all_comment)
                                
                            
                            if r1.start >= r2.start and r1.end <= r2.start or r1.start >= r2.end and r1.end <= r2.end:
                                delta = abs(latest_start - earliest_end)
                                delta = delta*60
                                overlap_time = str(timedelta(minutes=delta)).rsplit(':', 1)[0]
                                overlap_time_delta = timedelta(minutes=delta)
                                overlap_total += overlap_time_delta
                                # comment.append(str(j.task_manual_comments))
                                # all_comment = list(set(comment))
                                # all_comment = ', '.join(all_comment)


                    comment.append(str(j.task_manual_comments if j.task_manual_comments else ''))
                    all_comment = list(set(comment))
                    all_comment = ', '.join(all_comment)



            time_spent = i.x_time_spent
            
            # if i.time_spent:
            #     time_spent = datetime.strptime(str(i.x_time_spent), '%H:%M')
            # else:
            #     time_spent = datetime.strptime(str("00:00"), '%H:%M')
            if overlap_time == 0.0:                    
                overlap_time1 = date.strftime(datetime.strptime(str(overlap_total), '%H:%M:%S'), '%H:%M')
            else:
                overlap_time1 = date.strftime(datetime.strptime(str(overlap_total), '%H:%M:%S'), '%H:%M')
            # total_overlap +=overlap_time
            # print "\n\n______total_overlap________",total_overlap
            # task_priority = i.task_priority
            task_priority = dict(i._fields['task_priority'].selection).get(i.task_priority)
            task_type = dict(i._fields['task_type'].selection).get(i.task_type)
            task_status = dict(i._fields['state'].selection).get(i.state)
            print "\n\n___________task_status_________1680________",task_status
            task_name = i.name if i.name else " "
            start_date = i.estimated_start_date
            end_date = i.estimated_end_date
            user_pool = self.env['res.users']
            user_brws = user_pool.browse(SUPERUSER_ID)
            
            start_tz = pytz.utc.localize(parse(start_date))
            
            start_format = start_tz.strftime ("%Y-%m-%d")
            stop_tz = pytz.utc.localize(parse(end_date))
            
            stop_format = stop_tz.strftime ("%Y-%m-%d")
           
            deadline = i.deadline
            alloted_time = 0.0
            if i.task_allocated_time : 
                    alloted_time = i.task_allocated_time*3600
                    alloted_time_delta = timedelta(seconds=alloted_time)
                    alloted_time = str(timedelta(seconds=alloted_time))
            
            myDate = date.today()    
            dateStr = str(myDate.year) +"-" + str(myDate.month)+ "-" + str(myDate.day)
            
            start_date = datetime.strptime(dateStr,'%Y-%m-%d')
            delay = 0.0
            if i.deadline:
                end_date = datetime.strptime(i.deadline,'%Y-%m-%d')
                diff = ''
                if end_date < start_date:
                   diff = start_date - end_date
                   delay = diff.days
            
            manual_time = 0.0
            total_seconds = 0.0
            
            for j in i.task_manual_time:
                    
                date1 = j.task_manual_date
                date2 = datetime.today().strftime('%Y-%m-%d')
                if date1 == date2:
                    manual_time += j.task_manual_time
                    print "\n\n___manual_time_____1425________",manual_time
                
            # for p in j.task_manual_comments:
            #         comment = p.comments
            total_seconds = manual_time*60*60
            
            # cummulative = total_seconds + total_second
            # total_cummutative += cummulative
            
            
            # cummulative_time =  str(timedelta(seconds=cummulative))
            
            # total_active_time = total_cummutative - total_overlap
            # print "total_active_time===============",total_active_time
            
           
            
            timed_time_for_day =  timedelta(seconds=total_second)
              
            ideal_time1 = 0.0
          
          
            # if overlap_time1 > 0.0:
            #         ideal_time1 = 30600 - (total_second + total_seconds - overlap_time1)
                    
            total_working_time = 0.0
            if ideal_time1>0.0:
                total_working_time = 30600 - ideal_time1
                
            total_working_time =  str(timedelta(seconds=total_working_time))    
            ideal_time =  str(timedelta(seconds=ideal_time1))

            
            sr_no=sr_no+1
                
            worksheet.write(row,col,sr_no,data_format)
            # col += 1
            
            worksheet.write(row,col+1,task_priority,data_format)
            # col += 1
            worksheet.write(row,col+2,task_type,data_format)
            # col += 1
            worksheet.write(row,col+3,task_name,data_format)
            # col += 1
            worksheet.write(row,col+4,start_format,data_format)
            # col += 1
            worksheet.write(row,col+5,stop_format,data_format)
            # col += 1
            worksheet.write(row,col+6,task_status,data_format)
            # col += 1
            attended_time = "8:30:00"
            attended_time_delta = timedelta(hours=8,minutes=30)
            attended_time = datetime.strptime(attended_time, '%H:%M:%S')
            # worksheet.write(row,col+7,str(attended_time.time()),data_format)
            # col += 1
            worksheet.write(row,col+7,deadline,data_format)
            # col += 1
            if i.task_allocated_time :
                alloted_time1 = datetime.strptime(alloted_time,'%H:%M:%S')
                print "\n\n____alloted_time_delta____1651______",alloted_time_delta,type(alloted_time_delta)
                alloted_time2 = date.strftime(alloted_time1, '%H:%M')
                worksheet.write(row,col+8,alloted_time2,data_format)
            total_alloted += alloted_time_delta
            total_alloted_hr = total_alloted.days * 24
            total_alloted_min = total_alloted.seconds//3600
            total_alloted_sec = total_alloted.seconds // 60 % 60
            if total_alloted_sec < 10:
                total_alloted1 = str(total_alloted_hr + total_alloted_min) + ":"+"0" + str(total_alloted_sec)
            else:
                total_alloted1 = str(total_alloted_hr + total_alloted_min) + ":" + str(total_alloted_sec)

            # col += 1
            
            # col += 1 
            timed_time_for_day_hr = timed_time_for_day.days * 24
            timed_time_for_day_min = timed_time_for_day.seconds//3600
            timed_time_for_day_sec = timed_time_for_day.seconds // 60 % 60
            if timed_time_for_day_sec < 10:
                timed_time_for_day1 = str(timed_time_for_day_hr + timed_time_for_day_min) + ":"+"0" + str(timed_time_for_day_sec)
            else:
                timed_time_for_day1 = str(timed_time_for_day_hr + timed_time_for_day_min) + ":" + str(timed_time_for_day_sec)
            worksheet.write(row,col+10,timed_time_for_day1,data_format)

            total_timed_time += timed_time_for_day
            total_timed_time_hr = total_timed_time.days * 24
            total_timed_time_min = total_timed_time.seconds//3600
            total_timed_time_sec = total_timed_time.seconds // 60 % 60
            if total_timed_time_sec < 10:
                total_timed_time1 = str(total_timed_time_hr + total_timed_time_min) + ":"+"0" + str(total_timed_time_sec)
            else:
                total_timed_time1 = str(total_timed_time_hr + total_timed_time_min) + ":" + str(total_timed_time_sec)

            # col += 1
            manual_time = str(timedelta(seconds=total_seconds))
            manual_time_delta = timedelta(seconds=total_seconds)
            manual_time1 = datetime.strptime(manual_time, '%H:%M:%S')
            manual_time2 = date.strftime(manual_time1, '%H:%M')
            worksheet.write(row,col+11,manual_time2,data_format)

            total_manual += manual_time_delta
            total_manual_hr = total_manual.days * 24
            total_manual_min = total_manual.seconds//3600
            total_manual_sec = total_manual.seconds // 60 % 60
            if total_manual_sec < 10:
                total_manual1 = str(total_manual_hr + total_manual_min) + ":"+"0" + str(total_manual_sec)
            else:
                total_manual1 = str(total_manual_hr + total_manual_min) + ":" + str(total_manual_sec)



            date1 = datetime.strptime(start_format, '%Y-%m-%d')
            date1 = date.strftime(date1, '%Y-%m-%d')
            date2 = datetime.today()
            date2 = date.strftime(date2, '%Y-%m-%d')
            time_zero = datetime.strptime("00:00", '%H:%M') 
            cummulative_time1 = float(time_spent) + float(manual_time_delta.total_seconds())
            cummulative_time2 = timedelta(seconds=cummulative_time1)
            cummulative_time2_hr = cummulative_time2.days * 24
            cummulative_time2_min = cummulative_time2.seconds//3600
            cummulative_time2_sec = cummulative_time2.seconds // 60 % 60
            if cummulative_time2_sec < 10:
                cummulative_time3 = str(cummulative_time2_hr + cummulative_time2_min) + ":"+"0" + str(cummulative_time2_sec)
            else:
                cummulative_time3 = str(cummulative_time2_hr + cummulative_time2_min) + ":" + str(cummulative_time2_sec)
            worksheet.write(row,col+9,cummulative_time3,data_format)

            total_cummutative += cummulative_time2
            total_cummutative_hr = total_cummutative.days * 24
            total_cummutative_min = total_cummutative.seconds//3600
            total_cummutative_sec = total_cummutative.seconds // 60 % 60
            if total_cummutative_sec < 10:
                total_cummutative1 = str(total_cummutative_hr + total_cummutative_min) + ":"+"0" + str(total_cummutative_sec)
            else:
                total_cummutative1 = str(total_cummutative_hr + total_cummutative_min) + ":" + str(total_cummutative_sec)

            # col += 1
            time_zero = datetime.strptime("00:00", '%H:%M')
            # print "----------------------------------------",timed_time_for_day,manual_time_delta,overlap_time_delta
            
            total_work_for_day = abs((timed_time_for_day + manual_time_delta) - overlap_total)
            total_work_for_day_hr = total_work_for_day.days * 24
            total_work_for_day_min = total_work_for_day.seconds//3600
            total_work_for_day_sec = total_work_for_day.seconds // 60 % 60
            if total_work_for_day_sec < 10:
                total_work_for_day2 = str(total_work_for_day_hr + total_work_for_day_min) + ":"+"0" + str(total_work_for_day_sec)
            else:
                total_work_for_day2 = str(total_work_for_day_hr + total_work_for_day_min) + ":" + str(total_work_for_day_sec)
            worksheet.write(row,col+12,str(total_work_for_day2),data_format)

            time_zero = datetime.strptime("00:00", '%H:%M')
            # total_work_for_day2 = datetime.strptime(total_work_for_day2, '%H:%M')
            total_working += total_work_for_day
            total_working_hr = total_working.days * 24
            total_working_min = total_working.seconds//3600
            total_working_sec = total_working.seconds // 60 % 60
            if total_working_sec < 10:
                total_working1 = str(total_working_hr + total_working_min) + ":"+"0" + str(total_working_sec)
            else:
                total_working1 = str(total_working_hr + total_working_min) + ":" + str(total_working_sec)
            # col += 1
            x_timed_time = total_work_for_day #datetime.strptime(timed_time_for_day2, '%H:%M')
            x_manual_time = manual_time_delta #datetime.strptime(manual_time2, '%H:%M')
            
            
            worksheet.write(row,col+13,str(overlap_time1),data_format)

            time_zero = datetime.strptime("00:00", '%H:%M') 
            total_ovrlp += overlap_total
            # total_ovrlp1 = date.strftime(total_ovrlp, '%H:%M')
            # col += 1
            brk_time = datetime.strptime("00:30", '%H:%M')
            time_zero = datetime.strptime('00:00', '%H:%M')
            x_add_time = (x_timed_time  + x_manual_time)
            sub_overlap = abs(x_add_time - overlap_total)
            sub_overlap1 = sub_overlap #datetime.strptime(str(sub_overlap), '%H:%M:%S')
            sub_brk = attended_time - brk_time
            sub_brk1 = datetime.strptime(str(sub_brk), '%H:%M:%S')
            ideal_time = abs(sub_brk - sub_overlap1)
            
            # ideal_time3 = datetime.strptime(str(ideal_time), '%H:%M:%S')
            ideal_time2 = str(timedelta(seconds=ideal_time.seconds))
            # worksheet.write(row,col+14,str(ideal_time2),data_format)

            time_zero = datetime.strptime("00:00", '%H:%M')  
            ideal_time4 =  ideal_time                  
            total_ideal_time +=  ideal_time4
            total_ideal_time1 = str(timedelta(seconds=total_ideal_time.seconds))
            # col += 1
            if i.initial_completion:
                worksheet.write(row,col+14, str(i.initial_completion),data_format)
            else :
                worksheet.write(row,col+14, 0.0 ,data_format)

                    # col += 1
            worksheet.write(row,col+15,current_completion,data_format)
            # col += 1
            worksheet.write(row,col+16, difference,merge_format)
                    # col += 1

            if i.task_allocated_time :
                alloted_time2 = alloted_time_delta #datetime.strptime(alloted_time2,'%H:%M')
                variation = abs(alloted_time2 - x_timed_time)
                # variation1 = datetime.strptime(str(variation), '%H:%M:%S')
                variation2 = str(timedelta(seconds=variation.seconds))
                x_variation2 = date.strftime(datetime.strptime(str(variation2), '%H:%M:%S'), '%H:%M')
                worksheet.write(row,col+17,str(x_variation2),merge_format)
            else:
                worksheet.write(row,col+17,"00:00",merge_format)
            print "\n\n_________DELAY________",i.delay
            worksheet.write(row,col+18,delay,merge_format)
            if i.delay:
                print "\n\n________REASON_________",i.task_delay_reason
                worksheet.write(row,col+19,i.task_delay_reason,data_format)
            else:
                worksheet.write(row,col+19,'No Delay',data_format)
            worksheet.write(row,col+20,all_comment,data_format)
            # col += 1
            row +=1    

            
        total_overlap1 =  str(timedelta(seconds=total_ovrlp.seconds))
        total_active_time1 =  str(timedelta(seconds=total_active_time))
        # total_cummutative1 =  str(timedelta(seconds=total_cummutative))
        start_cell = nameBox(4,2)
        end_cell = nameBox(row,2)
        
        worksheet.write(row+8,1,'Reported Time:',data_format)
        reported_time = total_working1
        # reported_time1 = datetime.strptime(str(reported_time), '%H:%M')
        # reported_time2 = date.strftime(reported_time1, '%H:%M')
        # x_reported_time = date.strftime(datetime.strptime(str(reported_time), '%H:%M:%S'), '%H:%M')
        worksheet.write(row+8,2,reported_time,data_format)

        worksheet.write(row+9,1,'Overlaps:',data_format)
        x_total_ovrlp = date.strftime(datetime.strptime(str(total_ovrlp), '%H:%M:%S'), '%H:%M')
        worksheet.write(row+9,2,str(x_total_ovrlp),data_format)

        worksheet.write(row+10,1,'Active Time:',data_format)
        if total_working > total_ovrlp:
            active_time = total_working - total_ovrlp
        else:
            active_time = total_ovrlp - total_working
        active_time1 =str(timedelta(seconds=active_time.seconds))
        # active_time2 = date.strftime(active_time1, '%H:%M')
        x_active_time1 = date.strftime(datetime.strptime(str(active_time1), '%H:%M:%S'), '%H:%M')
        worksheet.write(row+10,2,str(x_active_time1),data_format)

        # worksheet.write(row+11,1,'Total Idle Time:',data_format)
        # x_total_ideal_time1 = date.strftime(datetime.strptime(str(total_ideal_time1), '%H:%M:%S'), '%H:%M')
        # worksheet.write(row+11,2,x_total_ideal_time1,data_format)
        worksheet.write(row+11,1,'Total Idle Time:',data_format)
        if attended_time_delta > active_time:
            gap = attended_time_delta - active_time
        else:
            gap = active_time - attended_time_delta
        # gap1 = datetime.strptime(str(gap), '%H:%M:%S')
        gap2 = str(timedelta(seconds=gap.seconds))
        x_gap2 = date.strftime(datetime.strptime(str(gap2), '%H:%M:%S'), '%H:%M')
        worksheet.write(row+11,2,str(x_gap2),data_format)

        worksheet.write(row+1,8,str(total_alloted1),header_format)   
        worksheet.write(row+1,9,str(total_cummutative1),header_format)   
        worksheet.write(row+1,10,str(total_timed_time1),header_format)   
        worksheet.write(row+1,11,str(total_manual1),header_format)   
        worksheet.write(row+1,12,reported_time,header_format)   
        worksheet.write(row+1,13,x_total_ovrlp,header_format)

        worksheet.write(row+5,1,'Time In:',data_format)
        worksheet.write(row+5,2,'10AM',data_format)
        worksheet.write(row+6,1,'Time Out:',data_format)
        worksheet.write(row+6,2,'7.30PM',data_format)
        worksheet.write(row+7,1,'Time :',data_format)
        worksheet.write(row+7,2,'8.30',data_format)

        workbook.close()
        out=base64.encodestring(fp.getvalue())
        data = (file_name,base64.b64decode(out))	
        cd=self.write({'excel_sheet1':out, 'file_name':file_name})
        return True                                                                                                                                                                                     
        
        
        
        # elif rec.report_type == 'work_group_classification':
        #     print "inside eliffff================"
        #     fp = StringIO()
        #     workbook = xls.Workbook(fp)
        #     
        #     header_format = workbook.add_format({
        #                                         'bold': 1,
        #                                         'align': 'center',
        #                                         'valign': 'vcenter',
        #                                         'text_wrap':1,
        #                                         'font_name':'Verdana',
        #                                         'font_size':10,
        #                                         })
        #     data_format = workbook.add_format({
        #                                         'align': 'center',
        #                                         'valign': 'vcenter',
        #                                         'text_wrap':1,
        #                                         'font_name':'Verdana',
        #                                         'font_size':10,
        #                                         })
        #     
        #     no_data_format = workbook.add_format({
        #                                         'align': 'center',
        #                                         'valign': 'vcenter',
        #                                         'text_wrap':1,
        #                                         'font_name':'Verdana',
        #                                         'font_size':10,
        #                                         'font_color':'red',
        #                                         })
        #     
        #     merge_format = workbook.add_format({
        #                                         'align': 'center',
        #                                         'valign': 'vcenter',
        #                                         })
        #     
        #     bold = workbook.add_format({'bold': True , 'bg_color':'#808080','font_color':'black'})
        #     file_name = 'Work Group Classification.xlsx'
        #     report_name = 'Work Group Classification'
        #     worksheet = workbook.add_worksheet(report_name)
        #     worksheet.set_column('A:A', 15)
        #     worksheet.set_column('B:B', 15)
        #     worksheet.set_column('C:C', 15)
        #     worksheet.set_column('D:D', 15)
        #     worksheet.set_column('E:E', 15)
        #     worksheet.set_column('F:F', 15)
        #     worksheet.set_column('G:G', 15)
        #     worksheet.set_column('H:H', 15)
        #     worksheet.set_column('I:I', 15)
        #     worksheet.set_column('J:J', 15)
        #     worksheet.set_column('K:K', 15)
        #     worksheet.set_column('L:L', 15)
        #     worksheet.set_column('M:M', 15)
        #     worksheet.set_column('N:N', 15)
        #     worksheet.set_column('O:O', 15)
        #     worksheet.set_column('P:P', 15)
        #     worksheet.set_column('Q:Q', 15)
        #     worksheet.set_column('R:R', 15)
        #     worksheet.set_column('S:S', 15)
        #     worksheet.set_column('T:T', 15)
        #     
        #     
        #     worksheet.write('A1:A1','Work Group Classification',header_format)
        #     worksheet.write('B1:B1','Task Name',header_format)
        #     worksheet.write('C1:C1','Start Date ',header_format)
        #     worksheet.write('D1:D1','End Date',header_format)
        #     worksheet.write('E1:E1','Task Status',header_format)
        #     worksheet.write('F1:F1','Attended Time for the day',header_format)
        #     worksheet.write('G1:G1','Allotted Time  for the day',header_format)
        #     worksheet.write('H1:H1','Profile Time',header_format)
        #     worksheet.write('I1:I1','Cummulative Time ',header_format)
        #     # worksheet.write('J1:J1','Cummulative Time',header_format)
        #     worksheet.write('J1:J1','Timed Time for day',header_format)
        #     worksheet.write('K1:K1','Manual Time for the day',header_format)
        #     worksheet.write('L1:L1','Total Working Time for the day',header_format)
        #     worksheet.write('M1:M1','Overlap Time for the day',header_format)
        #     worksheet.write('N1:N1','Idle Time for the day',header_format)
        #     worksheet.write('O1:O1','Initial % of Completion',header_format)
        #     worksheet.write('P1:P1','Current % of Completion',header_format)
        #     worksheet.write('Q1:Q1','% of Completion',header_format)
        #     worksheet.write('R1:R1','Comments',header_format)
        #     
        #     myDate = date.today()
        #     today_date =  str(myDate.month)+ "/" + str(myDate.day) + "/" + str(myDate.year)
        #     print "today_date===================",today_date
        #     print "myDate=====================",myDate
        #     task_search_ids = self.env['task.management'] .search([('state','in',['draft','drop','deffered','waiting','pause','completed','in_progress'])])
        #     # .search([('task_manual_time.task_manual_date','=',today_date)
        #     #     ,('assigned_to','=',self.employee_id.id),('state','in',['draft','drop','deffered','waiting','pause','completed','in_progress'])])
        #    
        #     print "task_search_ids=======================",task_search_ids
        #     row=1
        #     sr_no = 0
        #    
        #     for i in task_search_ids:
        #             temp_count = 0
        #             col=0
        #             temp_row = 0
        #            
        #             task_priority = i.task_priority
        #             task_type = i.task_type if i.task_type else " "
        #             task_name = i.name if i.name else " "
        #             start_date = i.estimated_start_date
        #             end_date = i.estimated_end_date
        #             user_pool = self.env['res.users']
        #             user_brws = user_pool.browse(SUPERUSER_ID)
        #             
        #             start_tz = pytz.utc.localize(parse(start_date))
        #             
        #             start_format = start_tz.strftime ("%Y-%m-%d")
        #             stop_tz = pytz.utc.localize(parse(end_date))
        #             
        #             stop_format = stop_tz.strftime ("%Y-%m-%d")
        #            
        #             task_status = i.state
        #             deadline = i.deadline
        #             alloted_time = i.task_allocated_time if i.task_allocated_time else 0.00
        #             
        #             myDate = date.today()    
        #             dateStr = str(myDate.year) +"-" + str(myDate.month)+ "-" + str(myDate.day)
        #             
        #             start_date = datetime.strptime(dateStr,'%Y-%m-%d')
        #             if i.deadline:
        #                 end_date = datetime.strptime(i.deadline,'%Y-%m-%d')
        #                 diff = ''
        #                 if end_date < start_date:
        #                    diff = start_date - end_date
        #                    delay = diff.days
        #             
        #             manual_time = 0.0
        #             for j in i.task_manual_time:
        #                 manual_time = j.task_manual_time
        #             task_completion_per = i.percantage_task_completion
        #             
        #             
        #             
        #             comment = i.observer_comments if i.observer_comments else "NA"
        #             
        #             sr_no=sr_no+1
        #             
        #             worksheet.write(row,col,sr_no,data_format)
        #             col += 1
        #          
        #             worksheet.write(row,col,task_name,data_format)
        #             col += 1
        #             worksheet.write(row,col,task_name,data_format)
        #             col += 1
        #             worksheet.write(row,col,start_format,data_format)
        #             col += 1
        #             worksheet.write(row,col,stop_format,data_format)
        #             col += 1
        #             worksheet.write(row,col,task_status,data_format)
        #             col += 1
        #             worksheet.write(row,col,task_status,data_format)
        #             col += 1
        #            
        #             worksheet.write(row,col,alloted_time,data_format)
        #             col += 1
        #             
        #             worksheet.write(row,col,stop_format,data_format)
        #             col += 1
        #             worksheet.write(row,col,stop_format,data_format)
        #             col += 1
        #             worksheet.write(row,col,manual_time,data_format)
        #             col += 1
        #             worksheet.write(row,col,task_completion_per,data_format)
        #             col += 1
        #             
        #             worksheet.write(row,col,delay,data_format)
        #             col += 1
        #             worksheet.write(row,col,comment,data_format)
        #             col += 1
        #             row +=1
        # 
        # 
        # 
        # 
        #     workbook.close()
        #     out=base64.encodestring(fp.getvalue())
        #     data = (file_name,base64.b64decode(out))	
        #     cd=self.write({'excel_sheet':out, 'file_name':file_name})
        #     print "cd===============================",cd
        #     return True
        # 

