from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError

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

class TaskReport(models.Model):
    _name = 'task.report'
    _description = 'Task status wise report'
   
    employee_id = fields.Many2one('res.users','Employee', default=lambda self: self.env.user)
    date_to = fields.Date("To Date")
    date_from = fields.Date("From Date")
    
    
    @api.multi
    def search_tree_view(self):
        report_tree = self.env.ref('Choice_org_addons.view_task_management_tree_report').id
        report_form =self.env.ref('Choice_org_addons.view_task_management_form').id
        report_search = self.env.ref('Choice_org_addons.view_task_management_filter').id
        search2 = []
        search = []
        model_id =''
        if self.date_from > self.date_to:
                 raise ValidationError(_('Please Select Proper Date.'))   
        todays_date = datetime.today().strftime('%Y-%m-%d')
        task_search_ids = self.env['task.management'].search([('current_date','=',todays_date),
                                            ('assigned_to','=',self.employee_id.id),
                                            ('state','!=','draft')])
            # ('state','in',['draft','drop','deffered','waiting','pause','completed','in_progress'])])
        
        print "task_search_ids=======================",task_search_ids
       
        for i in task_search_ids:
                temp_count = 0
                col=0
                temp_row = 0
                percent = 0.0
                total_second1=0.0
                total_second = 0.0
                
                for l in i.task_history :
                        date1 = l.task_history_date 
                        date2 = datetime.today().strftime('%Y-%m-%d')

                        if date1 == date2 :
                            total_second += l.task_spend_time
                        
                        if date1 < date2 or date1 == date2: 
                            percent = 0.0 
                            percent = l.task_percent_completion 
                            i.initial_completion = l.task_percent_completion 
                            i.current_completion = i.percantage_task_completion
                        
                            # percent = 0.0
                            # percent = l.task_percent_completion
                            # i.initial_completion = l.task_percent_completion 
                            # i.current_completion = i.percantage_task_completion

                
                difference = 0.0
                if i.current_completion > 0.0:
                    difference = float(i.current_completion) -float(i.initial_completion)


                # i.initial_completion = percent
                # i.current_completion = i.percantage_task_completion
                # task_completion_per = i.percantage_task_completion
                # difference = 0.0
                # if percent > 0.0:
                #         difference = task_completion_per - percent

                        
                alloted_time = 0.0
                if i.task_allocated_time : 
                    alloted_time = i.task_allocated_time*3600
                    alloted_time_delta = timedelta(seconds=alloted_time)
                    alloted_time = str(timedelta(seconds=alloted_time))
                
                i.completion = difference
                overlap_time = 0.0
                overlap_time1 =0.0
                overlap_time_delta = timedelta(minutes=0)
                overlap_total = timedelta(minutes=0)
                comment = []
                all_comment = ''
                a=[]
                for j in i.task_manual_time:
                    print "\n\n________Task Name________",i.name
                    for l in i.task_history :
                        date1 = l.task_history_date
                        date2 = datetime.today().strftime('%Y-%m-%d')
                        date3 = j.task_manual_date
                        if date1 == date2:
                            print "inside if condition -----------------------"
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
                                
                                # comment.append(str(j.task_manual_comments if j.task_manual_comments else ''))
                                # all_comment = list(set(comment))
                                # i.comment = ', '.join(all_comment)

                            if r1.start >= r2.start and r1.end <= r2.start or r1.start >= r2.end and r1.end <= r2.end:
                                delta = abs(latest_start - earliest_end)
                                delta = delta*60
                                overlap_time = str(timedelta(minutes=delta)).rsplit(':', 1)[0]
                                overlap_time_delta = timedelta(minutes=delta)
                                overlap_total += overlap_time_delta
                                # all_comment = list(set(comment))
                                # i.comment = ', '.join(all_comment)
                        print "task comment ---------------------",j.task_manual_comments
                        comment.append(str(j.task_manual_comments if j.task_manual_comments else ''))
                        all_comment = list(set(comment))
                        i.comment = ', '.join(all_comment)
                time_spent = i.x_time_spent
                # if i.time_spent:
                #     time_spent = datetime.strptime(str(i.time_spent), '%H:%M')
                # else:
                #     time_spent = datetime.strptime(str("00:00"), '%H:%M')
                if overlap_time == 0.0:                    
                    overlap_time1 = date.strftime(datetime.strptime(str(overlap_total), '%H:%M:%S'), '%H:%M')
                else:
                    overlap_time1 = date.strftime(datetime.strptime(str(overlap_total), '%H:%M:%S'), '%H:%M')

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
                       
                       
                i.delay = delay 
                manual_time = 0.0
                total_seconds = 0.0
                for j in i.task_manual_time:
                    date1 = j.task_manual_date
                    date2 = datetime.today().strftime('%Y-%m-%d')
                    if date1 == date2:
                        manual_time += j.task_manual_time

                    # if date1 == date2 :
                    #     manual_time1 += j.task_manual_time
                    # comment = j.task_manual_comments
                total_seconds = manual_time*60*60
                manual_time = str(timedelta(seconds=total_seconds))
                manual_time_delta = timedelta(seconds=total_seconds)
                manual_time1 = datetime.strptime(manual_time, '%H:%M:%S')
                manual_time2 = date.strftime(manual_time1, '%H:%M')    
                i.manual_time = manual_time2     
                # 
                total_seconds = manual_time*60*60
                start_date = i.estimated_start_date
                end_date = i.estimated_end_date
                user_pool = self.env['res.users']
                user_brws = user_pool.browse(SUPERUSER_ID)
                start_tz = pytz.utc.localize(parse(start_date))
                start_format = start_tz.strftime ("%Y-%m-%d")
                stop_tz = pytz.utc.localize(parse(end_date))
                stop_format = stop_tz.strftime ("%Y-%m-%d")

                
                time_zero = datetime.strptime("00:00", '%H:%M')
                timed_time_for_day =  timedelta(seconds=total_second)
                timed_time_for_day_hr = timed_time_for_day.days * 24
                timed_time_for_day_min = timed_time_for_day.seconds//3600
                timed_time_for_day_sec = timed_time_for_day.seconds // 60 % 60
                if timed_time_for_day_sec < 10:
                    timed_time_for_day1 = str(timed_time_for_day_hr + timed_time_for_day_min) + ":"+"0" + str(timed_time_for_day_sec)
                else:
                    timed_time_for_day1 = str(timed_time_for_day_hr + timed_time_for_day_min) + ":" + str(timed_time_for_day_sec)
                i.timed_time = timed_time_for_day1


                cummulative_time1 = float(time_spent) + float(manual_time_delta.total_seconds())
                cummulative_time2 = timedelta(seconds=cummulative_time1)

                cummulative_time2_hr = cummulative_time2.days * 24
                cummulative_time2_min = cummulative_time2.seconds//3600
                cummulative_time2_sec = cummulative_time2.seconds // 60 % 60
                if cummulative_time2_sec < 10:
                    cummulative_time3 = str(cummulative_time2_hr + cummulative_time2_min) + ":"+"0" + str(cummulative_time2_sec)
                else:
                    cummulative_time3 = str(cummulative_time2_hr + cummulative_time2_min) + ":" + str(cummulative_time2_sec)
                i.cummulative_time = cummulative_time3


                total_work_for_day = abs((timed_time_for_day + manual_time_delta) - overlap_total)
            # print "total work for the day ----------------------",total_work_for_day,type(total_work_for_day)
                total_work_for_day_hr = total_work_for_day.days * 24
                total_work_for_day_min = total_work_for_day.seconds//3600
                total_work_for_day_sec = total_work_for_day.seconds // 60 % 60
                if total_work_for_day_sec < 10:
                    total_work_for_day2 = str(total_work_for_day_hr + total_work_for_day_min) + ":"+"0" + str(total_work_for_day_sec)
                else:
                    total_work_for_day2 = str(total_work_for_day_hr + total_work_for_day_min) + ":" + str(total_work_for_day_sec)
                i.total_working_time = total_work_for_day2
                # attended_time =0.0
                # attended_time = 
                
                attended_time = datetime.strptime("08:30", '%H:%M')
                attended_time1 = date.strftime(attended_time, '%H:%M')
                i.attended_time = attended_time1
                
                i.overlap_time = overlap_time1
                # print "\n\n______i.overlap_time_______",i.overlap_time,type(overlap_time1)
                # brk_time = datetime.strptime("0:30:00", '%H:%M:%S')
                # time_zero = datetime.strptime('00:00:00', '%H:%M:%S')
                # x_timed_time = datetime.strptime(timed_time_for_day2, '%H:%M')
                # x_manual_time = datetime.strptime(manual_time2, '%H:%M')
                # x_add_time = (x_timed_time - time_zero + x_manual_time)
                # print "\n\n____attended_time_______",type(attended_time)
                # print "\n\n_______brk_time__________",type(brk_time)
                # print "\n\n_______time_zero__________",type(time_zero)
                # print "\n\n_______x_timed_time__________",type(x_timed_time)
                # print "\n\n_______x_manual_time__________",type(x_manual_time)
                # print "\n\n_______x_add_time__________",type(x_add_time)
                # ideal_time = attended_time - abs(x_add_time - overlap_time1 - brk_time)
                # ideal_time1 = date.strftime(ideal_time, '%H:%M')
                # i.ideal_time = ideal_time1
                # print "\n\n__________ideal_time_________",ideal_time1

                if i.task_allocated_time :
                    # print "ALLOTED time 2 =======================",alloted_time2
                    alloted_time2 = alloted_time_delta #datetime.strptime(alloted_time2,'%H:%M')
                    variation = abs(alloted_time2 - total_work_for_day)
                    # variation1 = datetime.strptime(str(variation), '%H:%M:%S')
                    variation2 = str(timedelta(seconds=variation.seconds))
                    x_variation2 = date.strftime(datetime.strptime(str(variation2), '%H:%M:%S'), '%H:%M')
                    i.variation = x_variation2
        
        return {
           'type': 'ir.actions.act_window',
           'name': 'Task Report',
           'res_model': 'task.management',
           'view_mode': 'form',
           'view_type': 'form',
           'domain': [('estimated_start_date','>=',self.date_from),('estimated_start_date','<=',self.date_to),
            ('assigned_to', '=',self.employee_id.id),('state','!=','draft')],
           'target': 'current',
           'views': [(report_tree, 'tree'),(report_form, 'form'),(report_search,'search')],
           'context': {'create': False,'edit': True,'remove_uid_domain': True},
        }