from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError, Warning

from lxml import etree
from operator import itemgetter

from datetime import datetime, date, time, timedelta
import math
import pytz
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT,DATETIME_FORMATS_MAP, float_compare

from dateutil.parser import parse

from datetime import timedelta
from dateutil.relativedelta import relativedelta, MO, TU, WE, TH, FR, SA, SU

#test comment 

def float_to_time(float_hour):
    return datetime.time(int(math.modf(float_hour)[1]), int(60 * math.modf(float_hour)[0]), 0)

class CommentsManagement(models.Model):
    _name = 'comments.management'
    _description = 'Comments Management'
    
    attachment = fields.Binary(string='Attachment', attachment=True)
    filename = fields.Char("Filename")
    comments = fields.Char(string='Comments')
    start_date = fields.Date(string='Start Date')
    task_id = fields.Many2one('task.management', string='Task')

class TaskManagement(models.Model):
    _name = 'task.management'
    _description = 'Task Management'
    _order = 'task_priority desc'
    
    AVAILABLE_PRIORITIES = [
                        ('0', 'Normal'),
                        ('1', 'Very low'),
                        ('2', 'Low'),
                        ('3', 'Medium'),
                        ('4', 'High'),
                        ('5', 'Very High'),
                    ]
    
    name = fields.Char(string='Task Name',help='Provide task name.')

    interval = fields.Integer(string="Repeat every", default=1)
    rrule_type = fields.Selection([
        ('daily', 'Day(s)'),
        ('weekly', 'Week(s)'),
        ('monthly', 'Month(s)'),
        ('yearly', 'Year(s)')
    ], string='Recurrency')
    # end_type = fields.Selection([
    #                             ('count','Number of repitations'),
    #                             ('end_date)','End date')
    #                             ], string="Until")
    end_type = fields.Selection([
                                ('count','Number of repitations')
                                ], string="Until")
    count = fields.Integer(string='Repeat', help="Repeat x times", default=1)
    final_date = fields.Date('Repeat Until')
    recurrency = fields.Boolean('Recurrent', help="Recurrent Task")
    month_by = fields.Selection([
                                ('date', 'Date of month'),
                                ('day', 'Day of month')
                                ], string='Option', default='date')
    day = fields.Integer('Date of month', default=1)
    week_list = fields.Selection([
        ('MO', 'Monday'),
        ('TU', 'Tuesday'),
        ('WE', 'Wednesday'),
        ('TH', 'Thursday'),
        ('FR', 'Friday'),
        ('SA', 'Saturday'),
        ('SU', 'Sunday')
    ], string='Weekday')
    byday = fields.Selection([
        ('1', 'First'),
        ('2', 'Second'),
        ('3', 'Third'),
        ('4', 'Fourth'),
        ('5', 'Fifth'),
        ('-1', 'Last')
    ], string='By day')

    mo = fields.Boolean('Mon')
    tu = fields.Boolean('Tue')
    we = fields.Boolean('Wed')
    th = fields.Boolean('Thu')
    fr = fields.Boolean('Fri')
    sa = fields.Boolean('Sat')
    su = fields.Boolean('Sun')

    recurrent_end_date = fields.Date(string="End date")

    subject = fields.Char(string='Subject',help='Provide subject for task.')
    task_type = fields.Selection([
                                    ('self_assigned', 'Self Assigned'),
                                    ('assigned', 'Assigned'),
                                    ('planned', 'Planned'),
                                    ('compulsory', 'Compulsory'),
                                    ], string='Task Type')
    task_priority = fields.Selection(AVAILABLE_PRIORITIES, default='0', index=True)
    reviewer = fields.Many2one('res.users', string='Reviewer')
    assigned_to = fields.Many2one('res.users', string='Assigned To')
    estimated_start_date = fields.Date(string='Estimated start date')
    estimated_end_date = fields.Date(string='Estimated end date')
    date_after_month = datetime.today()+ relativedelta(months=1)
    deadline = fields.Date(string='Deadline')
    description = fields.Html(string='Description')
    check_list_id = fields.One2many('check.list', 'task_id', 'Check List')
    state = fields.Selection([
                                ('draft', 'Not started'),
                                ('in_progress', 'In-Progress'),
                                ('completed', 'Completed'),
                                ('pause','Pause'),
                                ('waiting', 'Waiting on someone else'),
                                ('deferred', 'Postpone'),
                                ('drop', 'Drop'),
                                ], default='draft', string='Task Status')
    tag_ids = fields.Many2many('tags.config', 'task_tags_rel', 'task_id', 'tag_id', string='Tags')
    is_user_working = fields.Boolean(string="Is user working", default=False,copy=False)
    real_duration = fields.Float(string="Real Duration", default=0.0,copy=False)
    time_spent = fields.Char(string="Time Spent" , readonly=True, store=True,copy=False)
    x_time_spent = fields.Char("Time spent seconds")
    start_time = fields.Datetime(string="Start time", readonly=True, store=True,copy=False)
    pause_time = fields.Datetime(string="Pause time", readonly=True, store=True,copy=False)
    stop_time = fields.Datetime(string="Stop time", readonly=True, store=True,copy=False)
    reason_to_drop = fields.Char(string="Reason to drop task")
    task_drop_boolean = fields.Boolean(string="Drop Task",default=False,copy=False)
    task_reminder_check = fields.Boolean(string="Task reminder check", default=False,copy=False)
    task_reminder_date = fields.Datetime(string="Task reminder date-time",copy=False)
    task_reminder_mailto_selection = fields.Selection([
                                                ('self', 'Self'),
                                                ('to_creator', 'To creator'),
                                                ('to_responsible_person', 'To responsible person'),
                                                ], string='Mail to')
    
    task_reminder_mail_sent_check = fields.Boolean("Reminder mail sent",copy=False)
    project_id = fields.Many2one('project.project', string='Project')
    observer = fields.Many2many('res.users','res_users_task_managment_rel','task_id',string='Observer')
    progress = fields.Float(compute='_compute_task_delay', store=True, string='Working Time Recorded', group_operator="avg",copy=False)
    initial_progress = fields.Char('Initial Progress')
    current_progress = fields.Char('Current Progress')
    
    percantage_task_completion = fields.Float('Percentage of task completed(%)',copy=False)
    
    # comments = fields.Text("Comments")
    comment_id = fields.One2many('comments.management', 'task_id', 'Comments',copy=False)
    task_allocated_time = fields.Float("Allocated time", default=False)
    test_time =fields.Float("Test Time", default=False)
    task_manual_time = fields.Float("Manual Time",copy=False)
    task_exceeded_time = fields.Float("Exceeded Time",compute = "_compute_task_delay")
    task_exceeded_check = fields.Boolean("This task is exceded", default=False,compute = "_compute_task_delay")
    task_delay_reason = fields.Text("Reason")
    task_summary_id = fields.Many2one('task.summary','Task Summary')
    
    task_recurrent_check = fields.Boolean("Recurrent",copy=False)
    
    
    approval_status = fields.Selection([('waiting','Waiting'),
                                        ('approved','Approved'),
                                        ('reject','Rejected')
                                            ], default="waiting", string="Approval Status")
    task_reject = fields.Boolean('task reject')
    task_reject_comments = fields.Char('Task Review comments')
    task_manual_time = fields.One2many('manual.time', 'task_management_id', 'Manual Time')
    task_history = fields.One2many('task.history', 'task_history_id', 'History')
    task_history_id = fields.Many2one('task.history')
    observer_comments = fields.Text('Observer Comments')
    
    #new one2many added for observer comments above observer_comments is kept invisible
    observer_comments_ids = fields.One2many('observer.comments','task_mgmt_id',string='Observer Comments')
    
    cummulative_time = fields.Char('Cummulative Time')
    timed_time = fields.Char('Timed Time for the day')
    total_working_time = fields.Char('Total Working Time for the day')
    overlap_time =  fields.Char('Overlap Time for the day')
    ideal_time = fields.Char('Ideal Time for the day')
    # total_time = fields.Char('Total Time',compute='_total_time')
    initial_completion = fields.Char('Initial % of Completion')
    current_completion = fields.Char('Current % of Completion')
    completion = fields.Char(string='% of Completion')
    attended_time =  fields.Char('Attended Time for the day')
    delay = fields.Integer('Delay')
    comment = fields.Char('Comment')
    manual_time = fields.Char('Manual Time')
    task_allocated_time_new = fields.Char('Allocated Time')
    current_date = fields.Date('Current Date')
    variation = fields.Char('Variation')
    to_do_task = fields.Boolean('To-Do Task')
    check =fields.Boolean(' ')
    current_user = fields.Many2one('res.users','Employee', default=lambda self: self.env.user)
    # current_month_tasks = fields.Datetime(string="Current Month", default=time.strftime('%Y-01-01'))
    task_approve_check = fields.Boolean(string='')
    
    
    # #COmpute Total Time (total_time=cummulative_time+timed_time+total_working_time+overlap_time+manual_time)
    # @api.depends("cummulative_time","timed_time","total_working_time","overlap_time",'manual_time')
    # def _total_time(self):
    #     for rec in self:
    #         string=''
    #         cummulative_time=rec.cummulative_time.replace(":",'.'),
    #         cummulative_time=string.join(cummulative_time)
    #         timed_time=rec.timed_time.replace(":",'.'),
    #         timed_time=string.join(timed_time)
    #         total_working_time=rec.total_working_time.replace(":",'.'),
    #         total_working_time=string.join(total_working_time)
    #         overlap_time=rec.overlap_time.replace(":",'.'),
    #         overlap_time=string.join(overlap_time)
    #         manual_time=rec.manual_time.replace(":",'.'),
    #         manual_time=string.join(manual_time)
           
    #         total_time=float(cummulative_time)+float(timed_time)+float(total_working_time)+float(overlap_time)+float(manual_time)
    #         rec.total_time=str(total_time).replace(".",':')
            
        
        
    @api.model
    def create(self,vals):
        print "\n\n_________INSIDE CREATE___________________",vals
        object_id = super(TaskManagement, self).create(vals)
        ir_model_data = self.env['ir.model.data']
        print "\n\n_______ir_model_data______",ir_model_data
        template_id = ir_model_data.get_object_reference('Choice_org_addons', 'email_template_edi_task_assign')[1]
        template_brws = self.env['mail.template'].browse(template_id)
        print "\n\n________template_id_________template_brws________",template_id,template_brws
        if template_brws:
        	template_brws = self.env['mail.template'].browse(template_id)
        if template_brws:
            template_brws.send_mail(object_id.id, force_send=True)

        print "\n\n_________CURRENT DATE________",datetime.now()
        remainder_mail_id  = ir_model_data.get_object_reference('Choice_org_addons', 'email_template_edi_deadline_reminder')[1]
        # if task_reminder_date == 

        deadline_vals = vals.get('deadline')
        end_date_vals = vals.get('estimated_end_date')
        if deadline_vals < end_date_vals:
            print "aaaaaaaaaaaaaaaaaaaaaaaa"
            raise ValidationError(_("Entered deadline is less than end date."))

        x_start_date = vals.get('estimated_start_date')
        x_end_date = vals.get('estimated_end_date')
        x_date_after_month = vals.get('date_after_month')
        if x_start_date and x_date_after_month:
            start_date = datetime.strptime(x_start_date,'%Y-%m-%d')
            if start_date > x_date_after_month:
                raise ValidationError(_("Estimated Start Date:Start date should be on or before one month date from the current date"))
        
        if x_end_date and x_start_date:
            print "\nbbbbbbbbbbbbbbbb",x_end_date,x_start_date
            end_date = datetime.strptime(str(x_end_date),'%Y-%m-%d')
            start_date = datetime.strptime(str(x_start_date),'%Y-%m-%d')
            date_after_three_months = start_date + relativedelta(months=3)
            if end_date > date_after_three_months:
                raise ValidationError(_("Estimated Stop Date:Stop date should be on or before three months date from the start date"))
        
        return object_id
        
    @api.multi
    def write(self, vals):
        if vals:
            if vals.get('estimated_start_date') or vals.get('estimated_end_date'):
                start_date = datetime.strptime(vals.get('estimated_start_date') if vals.get('estimated_start_date') else self.estimated_start_date,'%Y-%m-%d')
                end_date = datetime.strptime(vals.get('estimated_end_date') if vals.get('estimated_end_date') else self.estimated_end_date,'%Y-%m-%d')
                if start_date > end_date:
                    raise ValidationError(_("Start date cannot be greater than end date."))    
        task_write = super(TaskManagement, self).write(vals)  
        
        return task_write

    @api.multi
    def create_recurrent_task(self):
        print "\n\n_____INSIDE RECURRENT TASK________________"
        if self.interval and self.interval < 0:
            raise UserError(_('interval cannot be negative.'))
        if self.count and self.count <= 0:
            raise UserError(_('Event recurrence interval cannot be negative.'))
        print "\n\n_______BEFORE VALS____________",self.observer.ids
        vals = {
                'name': self.name,
                'reviewer': self.reviewer.id,
                'assigned_to': self.assigned_to.id,
                'observer': [( 6, 0, self.observer.ids)],
                'project_id': self.project_id.id,
                'recurrency': False,
                }
        print "\n\n_____AFTER VALS_________"        
        if self.rrule_type == 'daily':
            print "\n\n_________DAILY__________"
            repeat_x_time = 0
            for i in range(0,self.count):
                repeat_x_time += self.interval
                start_date = (datetime.strptime(self.estimated_start_date,'%Y-%m-%d') + timedelta(days=int(repeat_x_time))).strftime('%Y-%m-%d')
                print "\n\n_______start_date_________estimated_start_date________",start_date,self.estimated_start_date
                print "\n\n______BEFORE DAILY VALS_______________"
                vals.update({
                            'estimated_start_date': start_date,
                            'estimated_end_date': start_date,
                            'deadline': start_date,
                        })
                print "\n\n____AFTER DAILY VALS__________________"
                self.env['task.management'].create(vals)
                print "\n\n______CREATE DAILY___________"

        if self.rrule_type == 'yearly':
            repeat_x_time = 0
            for i in range(0,self.count):
                repeat_x_time += self.interval
                start_date = datetime.strptime(self.estimated_start_date,'%Y-%m-%d') + relativedelta(years=+(int(repeat_x_time)))
                vals.update({
                            'estimated_start_date': start_date,
                            'estimated_end_date': start_date,
                            'deadline': start_date,
                        })
                self.env['task.management'].create(vals)

        if self.rrule_type == 'monthly':
            if self.month_by == 'date' and (self.day < 1 or self.day > 31):
                raise UserError(_("Please select a proper day of the month."))
            if self.month_by == 'date':
                repeat_x_month = 0
                for i in range(0,self.count):
                    repeat_x_month += self.interval
                    date = datetime.strptime(self.estimated_start_date,'%Y-%m-%d').replace(day=self.day) + relativedelta(months=+int(repeat_x_month))
                    vals.update({
                            'estimated_start_date': date,
                            'estimated_end_date': date,
                            'deadline': date,
                        })
                    self.env['task.management'].create(vals)
            else:
                repeat_x_month = 0
                for i in range(0,self.count):
                    repeat_x_month += self.interval
                    date = datetime.strptime(self.estimated_start_date,'%Y-%m-%d').replace(day=self.day) + relativedelta(months=+int(repeat_x_month))
                    if self.week_list == 'MO':
                        date_of_month = date + relativedelta(weekday=MO(int(self.byday)))
                    elif self.week_list == 'TU':
                        date_of_month = date + relativedelta(weekday=TU(int(self.byday)))
                    elif self.week_list == 'WE':
                        date_of_month = date + relativedelta(weekday=WE(int(self.byday)))
                    elif self.week_list == 'TH':
                        date_of_month = date + relativedelta(weekday=TH(int(self.byday)))
                    elif self.week_list == 'FR':
                        date_of_month = date + relativedelta(weekday=FR(int(self.byday)))
                    elif self.week_list == 'SA':
                        date_of_month = date + relativedelta(weekday=SA(int(self.byday)))
                    elif self.week_list == 'SU':
                        date_of_month = date + relativedelta(weekday=SU(int(self.byday)))
                    vals.update({
                            'estimated_start_date': date_of_month,
                            'estimated_end_date': date_of_month,
                            'deadline': date_of_month,
                        })
                    self.env['task.management'].create(vals)
        # print "\n\n____________WEEKLY________________"
        if self.rrule_type == 'weekly':
            # dow is Mon = 1, Sat = 6, Sun = 7
            # dow = day of week
            mon = 1
            tues = 2
            wed = 3
            thur = 4
            fri = 5
            sat = 6
            sun = 7
            week_date = datetime.strptime(self.estimated_start_date,'%Y-%m-%d').date()
            year, week, dow = week_date.isocalendar()
            if dow == 7:
                start_date = week_date
            else:
                start_date = week_date - timedelta(dow)
                end_date = start_date + timedelta(6)

            if self.mo:
                start_date = start_date + timedelta(mon)
                for i in range(0,self.count):
                    start_date += relativedelta(weekday=MO, weeks=self.interval)
                    vals.update({
                            'estimated_start_date': start_date,
                            'estimated_end_date': start_date,
                            'deadline': start_date,
                        })
                    self.env['task.management'].create(vals)
            elif self.tu:
                start_date = start_date + timedelta(tues)
                for i in range(0,self.count):
                    start_date += relativedelta(weekday=TU, weeks=self.interval)
                    vals.update({
                            'estimated_start_date': start_date,
                            'estimated_end_date': start_date,
                            'deadline': start_date,
                        })
                    self.env['task.management'].create(vals)
            elif self.we:
                start_date = start_date + timedelta(wed)
                for i in range(0,self.count):
                    start_date += relativedelta(weekday=WE, weeks=self.interval)
                    vals.update({
                            'estimated_start_date': start_date,
                            'estimated_end_date': start_date,
                            'deadline': start_date,
                        })
                    self.env['task.management'].create(vals)
            elif self.th:
                start_date = start_date + timedelta(thur)
                for i in range(0,self.count):
                    start_date += relativedelta(weekday=Th, weeks=self.interval)
                    vals.update({
                            'estimated_start_date': start_date,
                            'estimated_end_date': start_date,
                            'deadline': start_date,
                        })
                    self.env['task.management'].create(vals)
            elif self.fr:
                start_date = start_date + timedelta(fri)
                for i in range(0,self.count):
                    start_date += relativedelta(weekday=FR, weeks=self.interval)
                    vals.update({
                            'estimated_start_date': start_date,
                            'estimated_end_date': start_date,
                            'deadline': start_date,
                        })
                    self.env['task.management'].create(vals)
            elif self.sa:
                start_date = start_date + timedelta(sat)
                for i in range(0,self.count):
                    start_date += relativedelta(weekday=SA, weeks=self.interval)
                    vals.update({
                            'estimated_start_date': start_date,
                            'estimated_end_date': start_date,
                            'deadline': start_date,
                        })
                    self.env['task.management'].create(vals)
            elif self.su:
                start_date = start_date + timedelta(sat)
                for i in range(0,self.count):
                    start_date += relativedelta(weekday=SA, weeks=self.interval)
                    vals.update({
                            'estimated_start_date': start_date,
                            'estimated_end_date': start_date,
                            'deadline': start_date,
                        })
                    self.env['task.management'].create(vals)

    @api.multi
    def start_timer(self):
        task_search = self.env['task.management'].search([('is_user_working','=',True),('assigned_to','=',self._uid)])
        if task_search:
            raise ValidationError(_("There is a task already running. \n Pause or stop the current task to start this one."))
        else:
            if self.assigned_to.id == self._uid:
                current_time = datetime.now().time()
                self.is_user_working = True
                self.start_time = datetime.now()
                self.state = 'in_progress'
                self.current_date = datetime.now().date()
            else:
                raise ValidationError(_("You cannot start this task. It is not assigned to you."))
        
    @api.multi
    def stop_timer(self):
        
        if self.assigned_to.id == self._uid:
            self.is_user_working = False
            if self.state == 'in_progress':
                print "IN PROGRESS ====================",self.state
                self.pause_time = datetime.now()
                time = datetime.now()
                print "\n\n__________self.start_time_____________",self.start_time
                pause_time = datetime.strptime(self.pause_time,'%Y-%m-%d %H:%M:%S')
                start_time = datetime.strptime(self.start_time,'%Y-%m-%d %H:%M:%S')
                user_pool = self.env['res.users']
                user_brws = user_pool.browse(SUPERUSER_ID)
                tz = pytz.timezone(user_brws.partner_id.tz) or pytz.utc
                start_tz = pytz.utc.localize(parse(self.start_time)).astimezone(tz)
                stop_tz = pytz.utc.localize(parse(self.pause_time)).astimezone(tz)
                
                start_srt = start_tz.time().strftime('%H:%M:%S')
                stop_srt = stop_tz.time().strftime('%H:%M:%S')
                print "stat ============",start_srt,stop_srt
                x1 = time.strptime(start_srt.split(',')[0],'%H:%M:%S')
                x2 = time.strptime(stop_srt.split(',')[0],'%H:%M:%S')
                start_float = timedelta(hours=x1.hour,minutes=x1.minute,seconds=x1.second).total_seconds()/3600
                stop_float = timedelta(hours=x2.hour,minutes=x2.minute,seconds=x2.second).total_seconds()/3600
                print "X1=========================",start_float/3600,stop_float/3600

                time_diff = pause_time - start_time
                total_sec = time_diff.total_seconds()
                total_seconds = time_diff.total_seconds()
                
                total_seconds += self.real_duration

                print "total seconds ===================",total_seconds,time_diff,total_sec

                time_string = timedelta(seconds=total_seconds)
                
                # time_string = datetime.strptime(time_string, '%H:%M:%S')
                
                # time_string = date.strftime(time_string, '%H:%M')
                time_string_hr = time_string.days * 24
                time_string_min = time_string.seconds//3600
                time_string_sec = time_string.seconds // 60 % 60
                if time_string_sec < 10:
                    total_time_string = str(time_string_hr + time_string_min) + ":"+"0" + str(time_string_sec)
                    print "\n\n_________total_time_string________",total_time_string
                else:
                    total_time_string = str(time_string_hr + time_string_min) + ":" + str(time_string_sec)
                    print "\n\n_________total_time_string________",total_time_string
                self.real_duration = total_seconds
                
                if self.state == 'in_progress':
                    self.time_spent = total_time_string
                    self.x_time_spent = time_string.total_seconds()
                    # print "\n\n_____self.time_spent_______",self.time_spent
                self.state = 'completed'
                percent = self.percantage_task_completion
                prgrs = self.progress
                self.current_date = datetime.now().date()   
                for i in self:
                     i.task_history_id = self.env['task.history'].create({
                                                                            'task_history_date': datetime.now().date(),
                                                                            'task_start_time' : start_float,
                                                                            'task_stop_time' : stop_float,
                                                                            'task_spend_time': total_sec,
                                                                            'task_percent_completion': percent,
                                                                            'task_history_id': self.id,
                                                                            'progress_percent' : prgrs
                                                                            
                                                                        
                                                                                })
            else:
                print "PAUSE TIME =================",self.pause_time
                self.pause_time = datetime.now()
                time = datetime.now()
                print "\n\n__________self.start_time_____________",self.start_time
                pause_time = datetime.strptime(self.pause_time,'%Y-%m-%d %H:%M:%S')
                start_time = datetime.strptime(self.start_time,'%Y-%m-%d %H:%M:%S')
                user_pool = self.env['res.users']
                user_brws = user_pool.browse(SUPERUSER_ID)
                tz = pytz.timezone(user_brws.partner_id.tz) or pytz.utc
                start_tz = pytz.utc.localize(parse(self.start_time)).astimezone(tz)
                stop_tz = pytz.utc.localize(parse(self.pause_time)).astimezone(tz)
                
                start_srt = start_tz.time().strftime('%H:%M:%S')
                stop_srt = stop_tz.time().strftime('%H:%M:%S')
                print "stat ============",start_srt,stop_srt
                x1 = time.strptime(start_srt.split(',')[0],'%H:%M:%S')
                x2 = time.strptime(stop_srt.split(',')[0],'%H:%M:%S')
                start_float = timedelta(hours=x1.hour,minutes=x1.minute,seconds=x1.second).total_seconds()/3600
                stop_float = timedelta(hours=x2.hour,minutes=x2.minute,seconds=x2.second).total_seconds()/3600
                print "X1=========================",start_float/3600,stop_float/3600


                time_diff = pause_time - start_time
                total_sec = time_diff.total_seconds()
                total_seconds = time_diff.total_seconds()
                
                total_seconds = self.real_duration

                print "total seconds ===================",total_seconds,time_diff,total_sec

                time_string = timedelta(seconds=total_seconds)
                
                # time_string = datetime.strptime(time_string, '%H:%M:%S')
                
                # time_string = date.strftime(time_string, '%H:%M')
                time_string_hr = time_string.days * 24
                time_string_min = time_string.seconds//3600
                time_string_sec = time_string.seconds // 60 % 60
                if time_string_sec < 10:
                    total_time_string = str(time_string_hr + time_string_min) + ":"+"0" + str(time_string_sec)
                    print "\n\n_________total_time_string________",total_time_string
                else:
                    total_time_string = str(time_string_hr + time_string_min) + ":" + str(time_string_sec)
                    print "\n\n_________total_time_string________",total_time_string
                self.real_duration = total_seconds
                
                if self.state == 'in_progress':
                    self.time_spent = total_time_string 
                    self.x_time_spent = time_string.total_seconds()
                    print "\n\n_____self.time_spent_______",self.time_spent
                self.state = 'completed'
                percent = self.percantage_task_completion
                prgrs = self.progress
                self.current_date = datetime.now().date()

             
                
                
            
            task_summary_obj = self.env['task.summary']
            if self.assigned_to:
                task_summary_search = task_summary_obj.search([('timesheet_date','=',fields.Date.to_string(datetime.now().date())),
                    ('employee_id','=',self.assigned_to.id)])
                if task_summary_search:
                    self.task_summary_id = task_summary_search.id
                    
                else:
                    task_summary_create = task_summary_obj.create({'employee_id':self.assigned_to.id,
                                                'timesheet_date':datetime.now().date(),
                                                
                                               })
                    self.task_summary_id = task_summary_create.id
        else:
            raise ValidationError(_("You cannot Stop this task. It is not assigned to you."))
        
        
    @api.multi
    def pause_timer(self):
        if self.assigned_to.id == self._uid:
            self.is_user_working = False
            self.pause_time = datetime.now()
            time = datetime.now()
            print "\n\n__________self.start_time_____________",self.start_time
            pause_time = datetime.strptime(self.pause_time,'%Y-%m-%d %H:%M:%S')
            start_time = datetime.strptime(self.start_time,'%Y-%m-%d %H:%M:%S')
            user_pool = self.env['res.users']
            user_brws = user_pool.browse(SUPERUSER_ID)
            tz = pytz.timezone(user_brws.partner_id.tz) or pytz.utc
            start_tz = pytz.utc.localize(parse(self.start_time)).astimezone(tz)
            stop_tz = pytz.utc.localize(parse(self.pause_time)).astimezone(tz)
            
            start_srt = start_tz.time().strftime('%H:%M:%S')
            stop_srt = stop_tz.time().strftime('%H:%M:%S')
            print "stat ============",start_srt,stop_srt
            x1 = time.strptime(start_srt.split(',')[0],'%H:%M:%S')
            x2 = time.strptime(stop_srt.split(',')[0],'%H:%M:%S')
            start_float = timedelta(hours=x1.hour,minutes=x1.minute,seconds=x1.second).total_seconds()/3600
            stop_float = timedelta(hours=x2.hour,minutes=x2.minute,seconds=x2.second).total_seconds()/3600
            print "X1=========================",start_float/3600,stop_float/3600



            time_diff = pause_time - start_time
            
            total_sec = float(time_diff.total_seconds())
            
            total_seconds = time_diff.total_seconds()
            total_seconds += self.real_duration
            time_string = timedelta(seconds=total_seconds)
            print "\n\n________time_string____575___",time_string.total_seconds()
            # time_string = datetime.strptime(time_string, '%H:%M:%S')
            # time_string = date.strftime(time_string, '%H:%M')
            time_string_hr = time_string.days * 24
            time_string_min = time_string.seconds//3600
            time_string_sec = time_string.seconds // 60 % 60
            if time_string_sec < 10:
                total_time_string = str(time_string_hr + time_string_min) + ":"+"0" + str(time_string_sec)
            else:
                total_time_string = str(time_string_hr + time_string_min) + ":" + str(time_string_sec)
            self.real_duration = total_seconds
            print "\n\n_______total_time_string__________",total_time_string
            self.time_spent = total_time_string
            self.x_time_spent = time_string.total_seconds()
            print "\n\n_______self.x_time_spent________",self.x_time_spent
            percent = self.percantage_task_completion
            prgrs = self.progress
            print "\n\n_________prgrs__________",prgrs
            self.current_date = datetime.now().date()
            
            
            self.state = 'pause'
            for i in self:
                i.task_history_id = self.env['task.history'].create({
                                                                        'task_history_date': datetime.now().date(),
                                                                        'task_start_time' : start_float,
                                                                        'task_stop_time' : stop_float,
                                                                        'task_spend_time': total_sec,
                                                                        'task_percent_completion': percent,
                                                                        'task_history_id': self.id,
                                                                        'progress_percent':prgrs
                                                                    
                                                                            })
                
          
            
        else:
            raise ValidationError(_("You cannot Pause this task. It is not assigned to you."))
        
    
    @api.multi
    def deffered(self):
        if self.assigned_to.id == self._uid:
            self.is_user_working = False
            self.pause_time = datetime.now()
            time = datetime.now()
            print "\n\n__________self.start_time_____________",self.start_time
            pause_time = datetime.strptime(self.pause_time,'%Y-%m-%d %H:%M:%S')
            start_time = datetime.strptime(self.start_time,'%Y-%m-%d %H:%M:%S')
            user_pool = self.env['res.users']
            user_brws = user_pool.browse(SUPERUSER_ID)
            tz = pytz.timezone(user_brws.partner_id.tz) or pytz.utc
            start_tz = pytz.utc.localize(parse(self.start_time)).astimezone(tz)
            stop_tz = pytz.utc.localize(parse(self.pause_time)).astimezone(tz)
            
            start_srt = start_tz.time().strftime('%H:%M:%S')
            stop_srt = stop_tz.time().strftime('%H:%M:%S')
            print "stat ============",start_srt,stop_srt
            x1 = time.strptime(start_srt.split(',')[0],'%H:%M:%S')
            x2 = time.strptime(stop_srt.split(',')[0],'%H:%M:%S')
            start_float = timedelta(hours=x1.hour,minutes=x1.minute,seconds=x1.second).total_seconds()/3600
            stop_float = timedelta(hours=x2.hour,minutes=x2.minute,seconds=x2.second).total_seconds()/3600
            print "X1=========================",start_float/3600,stop_float/3600

            time_diff = pause_time - start_time
            print "\n\n__________time_diff__________",time_diff
            total_sec = time_diff.total_seconds()
            total_seconds = time_diff.total_seconds()
            total_seconds += self.real_duration
            time_string = timedelta(seconds=total_seconds)
            # time_string = datetime.strptime(time_string, '%H:%M:%S')
            # print "\n\n_________time_string___1111____",time_string, type(time_string)
            # time_string = date.strftime(time_string, '%H:%M')
            # print "\n\n_________time_string___2222____",time_string, type(time_string)
            time_string_hr = time_string.days * 24
            time_string_min = time_string.seconds//3600
            time_string_sec = time_string.seconds // 60 % 60
            if time_string_sec < 10:
                total_time_string = str(time_string_hr + time_string_min) + ":"+"0" + str(time_string_sec)
                print "\n\n_________total_time_string________",total_time_string
            else:
                total_time_string = str(time_string_hr + time_string_min) + ":" + str(time_string_sec)
                print "\n\n_________total_time_string________",total_time_string
            self.real_duration = total_seconds
            if self.state == 'in_progress':
                self.time_spent = total_time_string
                self.x_time_spent = time_string.total_seconds()

            # self.time_spent = time_string
            self.state = 'deferred'
            percent = self.percantage_task_completion
            prgrs = self.progress
            
            res_users = self.env['res.users'].search([('lang','in',['en_US'])])
            a = res_users[0]
            comp_email = a.company_id.email
            
            ir_model_data = self.env['ir.model.data']
            try:
                template_id = ir_model_data.get_object_reference('Choice_org_addons', 'email_template_deffered_task')[1]
            except ValueError:
                template_id = False
            template_brws = self.env['mail.template'].browse(template_id)
            if template_brws:
                template_brws = self.env['mail.template'].browse(template_id)
                
            if template_brws:
                template_brws.write({'email_from': comp_email,'email_to': self.reviewer.login })
                template_brws.send_mail(self.id, force_send=True)
            
            for i in self:
                i.task_history_id = self.env['task.history'].create({
                                                                        'task_history_date': datetime.now().date(),
                                                                        'task_start_time' : start_float,
                                                                        'task_stop_time' : stop_float,
                                                                        'task_spend_time': total_sec,
                                                                        'task_percent_completion': percent,
                                                                        'task_history_id': self.id,
                                                                        'progress_percent': prgrs
                                                                            })
            
            
        else:
            raise ValidationError(_("You cannot postpone this task. It is not assigned to you."))
    
    
    
    
    @api.multi
    def waiting(self):
        if self.assigned_to.id == self._uid:
            self.is_user_working = False
            self.pause_time = datetime.now()
            time = datetime.now()
            print "\n\n__________self.start_time_____________",self.start_time
            pause_time = datetime.strptime(self.pause_time,'%Y-%m-%d %H:%M:%S')
            start_time = datetime.strptime(self.start_time,'%Y-%m-%d %H:%M:%S')
            user_pool = self.env['res.users']
            user_brws = user_pool.browse(SUPERUSER_ID)
            tz = pytz.timezone(user_brws.partner_id.tz) or pytz.utc
            start_tz = pytz.utc.localize(parse(self.start_time)).astimezone(tz)
            stop_tz = pytz.utc.localize(parse(self.pause_time)).astimezone(tz)
            
            start_srt = start_tz.time().strftime('%H:%M:%S')
            stop_srt = stop_tz.time().strftime('%H:%M:%S')
            print "stat ============",start_srt,stop_srt
            x1 = time.strptime(start_srt.split(',')[0],'%H:%M:%S')
            x2 = time.strptime(stop_srt.split(',')[0],'%H:%M:%S')
            start_float = timedelta(hours=x1.hour,minutes=x1.minute,seconds=x1.second).total_seconds()/3600
            stop_float = timedelta(hours=x2.hour,minutes=x2.minute,seconds=x2.second).total_seconds()/3600
            print "X1=========================",start_float/3600,stop_float/3600

            time_diff = pause_time - start_time
            total_sec = time_diff.total_seconds()
            total_seconds = time_diff.total_seconds()
            total_seconds += self.real_duration
            time_string = timedelta(seconds=total_seconds)
            # time_string = datetime.strptime(time_string, '%H:%M:%S')
            # print "\n\n_________time_string___1111____",time_string, type(time_string)
            # time_string = date.strftime(time_string, '%H:%M')
            # print "\n\n_________time_string___2222____",time_string, type(time_string)
            time_string_hr = time_string.days * 24
            time_string_min = time_string.seconds//3600
            time_string_sec = time_string.seconds // 60 % 60
            if time_string_sec < 10:
                total_time_string = str(time_string_hr + time_string_min) + ":"+"0" + str(time_string_sec)
                print "\n\n_________total_time_string________",total_time_string
            else:
                total_time_string = str(time_string_hr + time_string_min) + ":" + str(time_string_sec)
                print "\n\n_________total_time_string________",total_time_string
            self.real_duration = total_seconds
            if self.state == 'in_progress':
                self.time_spent = total_time_string
                self.x_time_spent = time_string.total_seconds()

            # self.time_spent = time_string
            self.state = 'waiting'
            percent = self.percantage_task_completion
            prgrs = self.progress
            for i in self:
                i.task_history_id = self.env['task.history'].create({
                                                                        'task_history_date': datetime.now().date(),
                                                                        'task_start_time' : start_float,
                                                                        'task_stop_time' : stop_float,
                                                                        'task_spend_time': total_sec,
                                                                        'task_percent_completion': percent,
                                                                        'task_history_id': self.id,
                                                                        'progress_percent' : prgrs
                                                                    
                                                                            })
        else:
            raise ValidationError(_("You cannot put on waiting this task. It is not assigned to you."))
        
    @api.multi
    def drop_task(self):
        if self.assigned_to.id == self._uid:
            self.is_user_working = False
            self.task_drop_boolean = True
            self.state = 'drop'
            
            res_users = self.env['res.users'].search([('lang','in',['en_US'])])
            a = res_users[0]
            comp_email = a.company_id.email
            
            ir_model_data = self.env['ir.model.data']
            try:
                template_id = ir_model_data.get_object_reference('Choice_org_addons', 'email_template_drop_task')[1]
            except ValueError:
                template_id = False
            template_brws = self.env['mail.template'].browse(template_id)
            if template_brws:
                template_brws = self.env['mail.template'].browse(template_id)
                
            if template_brws:
                template_brws.write({'email_from': comp_email,'email_to': self.reviewer.login })
                template_brws.send_mail(self.id, force_send=True)
        else:
            raise ValidationError(_("You cannot Drop this task. It is not assigned to you."))
     
    @api.depends('real_duration','task_allocated_time')
    def _compute_task_delay(self):
        for i in self:
            if (i.real_duration > 0) and (i.task_allocated_time > 0):
                real_time_taken = i.real_duration
                task_allocated_time = i.task_allocated_time
                print "REAL TIME __________",real_time_taken
                print "Allocated  TIME __________",task_allocated_time
                task_allocated_time_hours = int(task_allocated_time)
                print "TASK allocated time hours ====",task_allocated_time_hours
                task_allocated_time_minute = (task_allocated_time-task_allocated_time_hours)*60
                print "TASK allocated time mins ====",task_allocated_time_minute
                task_allocated_time_obj = timedelta(hours=task_allocated_time_hours, minutes=task_allocated_time_minute)
 
                task_allocated_time_seconds = task_allocated_time_obj.seconds
                print "Task allocated time seconds--------",task_allocated_time_seconds
                i.task_exceeded_time = task_allocated_time_seconds - real_time_taken
                print "TASK exceeded time ----------------",i.task_exceeded_time
                
                i.progress = round(100*(real_time_taken/task_allocated_time_seconds),2)
                
                if task_allocated_time_seconds < real_time_taken:
                    i.task_exceeded_check = True
              
            
    @api.onchange('task_type')
    def _onchange_task_type(self):
        if self.task_type == 'self_assigned':
            self.assigned_to = self._uid
        else:
            self.assigned_to = False
            
      
    
    
    @api.onchange('estimated_start_date','estimated_end_date',)
    def _onchange_estimated_date(self):
        if self.estimated_start_date  and self.estimated_end_date:
            start_date = datetime.strptime(self.estimated_start_date,'%Y-%m-%d')
            end_date = datetime.strptime(self.estimated_end_date,'%Y-%m-%d')
            if start_date > end_date:
                raise ValidationError(_("Start date cannot be greater than end date."))
            

    @api.onchange('date_after_month','estimated_start_date')
    def _onchange_one_month(self):
        if self.estimated_start_date and self.date_after_month:
            start_date = datetime.strptime(self.estimated_start_date,'%Y-%m-%d')
            if start_date > self.date_after_month:
                raise ValidationError(_("Estimated Start Date:Start date should be on or before one month date from the current date"))


    @api.onchange('estimated_end_date','estimated_start_date')
    def _onchange_three_month(self):
        print "\n\n______self.estimated_start_date__________",self.estimated_start_date
        print "\n\n_________self.estimated_end_date_________",self.estimated_end_date
        if self.estimated_end_date and self.estimated_start_date:
            end_date = datetime.strptime(str(self.estimated_end_date),'%Y-%m-%d')
            start_date = datetime.strptime(str(self.estimated_start_date),'%Y-%m-%d')
            date_after_three_months = start_date + relativedelta(months=3)
            if end_date > date_after_three_months:
                raise ValidationError(_("Estimated Stop Date:Stop date should be on or before three months date from the start date"))


    @api.onchange('deadline','estimated_end_date')
    def _oncahnge_deadline(self):
        print "\n\n____oncahnge_deadline_____",self.deadline,self.estimated_end_date
        if self.deadline and self.estimated_end_date:
            end_date = datetime.strptime(self.estimated_end_date,'%Y-%m-%d')
            deadline = datetime.strptime(self.deadline,'%Y-%m-%d')
            if deadline < end_date:
                self.deadline = False
                raise ValidationError(_("Entered deadline is less than end date."))
    

    # @api.model
    # def create(self,vals):
    #     object_id = super(TaskManagement, self).create(vals)
    #     print "\n\n_________object_id___________",object_id
    #     print "\n\n______vals_______",vals
    #     x_start_date = vals.get('estimated_start_date')
    #     x_end_date = vals.get('estimated_start_date')
    #     if x_end_date and x_start_date:
    #         end_date = datetime.strptime(str(x_end_date),'%Y-%m-%d')
    #         start_date = datetime.strptime(str(x_start_date),'%Y-%m-%d')
    #         date_after_three_months = start_date + relativedelta(months=3)
    #         if end_date > date_after_three_months:
    #             raise ValidationError(_("Estimated Stop Date:Stop date should be on or before three months date from the start date"))  
    #     return object_id
    # @api.model
    # def create(self, vals):
    #     record = super(TaskManagement, self).create(vals)
    #     print "\n\n======vals=====", vals
    #     print "\n\n ======record====", record
    #     d = vals.values()[-1]
    #     print "\n\n ======record.values[-1]=====", d
    #     print "\n\n===estimated_end_date===",self.estimated_end_date
    #     print "\n\n===deadline===",self.deadline
    #     if self.deadline and self.estimated_end_date:
    #         end_date = datetime.strptime(self.estimated_end_date,'%Y-%m-%d')
    #         print "\n\n===end_date===",end_date
    #         # deadline = datetime.strptime(self.deadline,'%Y-%m-%d')
    #         # print "\n\n===deadline===",deadline
    #         if deadline < end_date:
    #             self.deadline = False
    #             raise ValidationError(_("Entered deadline is less than end date."))
    #     return record
   
    @api.model
    def _cron_deadline_reminder(self):
        su_id = self.env['res.partner'].browse(SUPERUSER_ID)
        for task in self.env['task.management'].search([('state','in',['draft'])]):
            if task.task_reminder_check == True:
                if task.task_reminder_mail_sent_check == False:
                    # reminder_date = datetime.strptime(task.task_reminder_date,'%Y-%m-%d').date()
                    reminder_date = task.task_reminder_date
                    today = datetime.now().date()
                    if reminder_date == today:
                        # if reminder_date.month == today.month:
                        #     if reminder_date.day == reminder_date.day:
                        template_id = self.env.ref('Choice_org_addons.email_template_edi_deadline_reminder')
                        if template_id:
                            values = template_id.generate_email(task.id, fields=None)
                            values['email_from'] = task.reviewer.partner_id.email
                            values['email_to'] = task.assigned_to.partner_id.email
                            values['res_id'] = False
                            mail_mail_obj = self.env['mail.mail']
                            msg_id = mail_mail_obj.create(values)
                            if msg_id:
                                msg_id.send()
                                task.write({'task_reminder_mail_sent_check' : True})
        return True
    
    @api.model
    def _cron_daily_report(self):
        todays_date = datetime.today().strftime('%Y-%m-%d')
        
        for task in self.env['task.management'].search([('task_history.task_history_date','=',todays_date)]):
            email_id = task.assigned_to.task.assigned_to.partner_id.email
            login=[]
            login.append(i.email_id)
            mail_ids=','.join(map(str,login))
            res_users = self.env['res.users'].search([('lang','in',['en_US'])])
            a = res_users[0]
            comp_email = a.company_id.email
           
            # for i in res_users:
            #     login.append(i.login)
            
            ir_model_data = self.env['ir.model.data']
            try:
                template_id = ir_model_data.get_object_reference('Choice_org_addons', 'email_template_edi_daily_task')[1]
            except ValueError:
                template_id = False
            template_brws = self.env['mail.template'].browse(template_id)
            if template_brws:
                template_brws = self.env['mail.template'].browse(template_id)
                
            if template_brws:
                template_brws.write({'email_from': comp_email,'email_to': mail_ids })
                template_brws.send_mail(self.id, force_send=True)
            return True
            
            
       
    @api.multi
    def approve_task(self):
        print "\n\n_____INSIDE APPROVE TASK______",self
        for i in self:
            print "\n\n__________i__________",i
            if i.task_summary_id:
                print "\n\n__________i.task_summary_id___________",i.task_summary_id
                if (i.task_summary_id.reviewer_id.id == self._uid) or (self._uid == 1):
                    print "\n\n_________i.approval_status _____________",i.approval_status 
                    i.approval_status = 'approved'
                    print("approved")
                else:
                    raise ValidationError(_("You donot have permission to approve this task."))
        
    @api.multi
    def reject_task(self):
        for i in self:
        
            if i.task_summary_id:
                if (i.task_summary_id.reviewer_id.id == self._uid) or (self._uid == 1):
                    i.approval_status = 'reject'
                    i.task_reject = True
                else:
                    raise ValidationError(_("You donot have permission to reject this task."))

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        
        res = super(TaskManagement, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(res['arch'])
        
        for node in doc.xpath("//form/notebook/page[@name='observer_comments']"):
            # print(node)
            node.set('invisible','1')
        res['arch'] = etree.tostring(doc)
        # print(res)
        return res

    @api.model
    def check_mail_task(self):
        print "\n\n________DEF CHECKING MAIL__________",self.env['res.users']
        #user = self.env['res.users'].browse([('user_id', '=', self.env.uid)])
        self._cr.execute("select id from res_users;")
        user = self._cr.fetchall()
        print "\n\n____________user____________",user
        for i in user: 
            print "\n\n_______i[0]____________",i[0]
            todays_date = datetime.now().date()
            print "\n\n________todays_date__________",todays_date
            task_name = "Checking Mails"
            vals = {'name':task_name,
                    'estimated_start_date':todays_date,
                    'estimated_end_date':todays_date,
                    'deadline':todays_date,
                    'state':'draft',
                    'task_type':'self_assigned',
                    'assigned_to': i[0],
                    'reviewer':1,
                    'assigned':1
                    
                    }
            print "\n\n________vals__________",vals
            a = self.env['task.management'].create(vals)
            print "\n\n______TASK RECORD__________",self.start_time

    @api.model
    def cron_remainder_task(self):
        print "\n\n______TASK REMAINDER CHECK_______"
        object_id = self.env['task.management'].search([('task_reminder_check','=',True)])
        print "\n\n___________object_id______________",object_id
        ir_model_data = self.env['ir.model.data']
        current_datetime = datetime.now()
        for task in object_id:
            if task.task_reminder_check == True:
                print "\n\n_______task_reminder_date________",task.task_reminder_date,task
                if task.task_reminder_date == current_datetime:
                    remainder_mail_id  = ir_model_data.get_object_reference('Choice_org_addons', 'email_template_edi_deadline_reminder')[1]
                    print "\n\n___________remainder_mail_id____________",remainder_mail_id
                    remainder_brws = self.env['mail.template'].browse(remainder_mail_id)
                    print "\n\n________remainder_brws_____________",remainder_brws
                    if task.task_reminder_mailto_selection == 'to_responsible_person':
                        remainder_brws.send_mail(object_id.id, force_send=True)

    @api.model
    def cron_recreate_task(self):
        object_id = self.env['task.management'].search([('approval_status','=','reject')])
        ir_model_data = self.env['ir.model.data']
        
        srch_rjctd_task = self.env['task.management'].search([('approval_status','=','reject')])
        
        for tasks in srch_rjctd_task:
            if tasks.approval_status == 'reject':
                tasks.state = 'draft'
                tasks.approval_status = 'waiting'

                template_id = ir_model_data.get_object_reference('Choice_org_addons', 'mail_on_rejection_of_task')[1]
                template_brws = self.env['mail.template'].browse(template_id)
                template_brws.send_mail(tasks.id, force_send=True)

                
class manual_time(models.Model):
    _name = 'manual.time'
    _description = 'Manual time entry for task'
    
    task_manual_date = fields.Date('Date',default=fields.Date.today())
    task_start_time = fields.Float('Start Time', default=False)
    task_end_time = fields.Float('End Time')
    task_manual_time = fields.Float('Time Spend')
    task_manual_comments = fields.Char('Comments')
    task_management_id = fields.Many2one('task.management','Task Management')
    
    # task_boolean = fields.Boolean('Start Boolean')
    
    # @api.model
    # def create(self,vals):
    #     object_id = super(manual_time, self).create(vals)
    #     print "\n\n_______vals____mmmmm___",vals
    #     print "\n\n________start_time___________",start_time
    #     if start_time:
    #         print "\n\n_____self.task_boolean_______",self.task_boolean
    #         self.task_boolean = True
    #         print "\n\n_____self.task_boolean_______",self.task_boolean



    @api.onchange('task_start_time','task_end_time')
    def _onchange_task_type(self):
        
        if self.task_start_time and self.task_end_time:
            
            task_manual_time = abs(self.task_end_time - self.task_start_time)
            # task_manual_time2 = datetime.strptime(str(task_manual_time), '%H.%M')
            # task_manual_time3 = date.strftime(task_manual_time2, '%H:%M')
            self.task_manual_time = task_manual_time

        if self.task_start_time > 24:
            raise Warning(_("Invalid Time"))
        if self.task_end_time > 24:
            raise Warning(_("Invalid Time"))
       
       
class task_history(models.Model):
    _name = 'task.history'
    _description = 'Daily History of Task'
    
    task_history_date = fields.Date('Date')
    task_spend_time = fields.Float('Spend Time')
    task_percent_completion = fields.Float('Percentage Completion')
    progress_percent = fields.Float('Progress Percentage')
    task_history_id = fields.Many2one('task.management','Task Management')
    task_start_time = fields.Float("Start Time")
    task_stop_time = fields.Float("Stop Time")

class ObserverComments(models.Model):
    _name = 'observer.comments'
    _description = 'Observer comments'
    
    name = fields.Text('Comments')
    observer_timestamp = fields.Datetime('Date')
    task_mgmt_id = fields.Many2one('task.management',string='Task')

