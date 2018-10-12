from lxml import etree

from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError
from odoo.osv.orm import setup_modifiers
import task_management

class TaskSummary(models.Model):
    _name = 'task.summary'
    _description = 'Summary of daily task'
    
    employee_id = fields.Many2one('res.users','Employee')
    reviewer_id = fields.Many2one('res.users','Reviewer')
    timesheet_date = fields.Date('Dated')
    task_summary = fields.One2many('task.management', 'task_summary_id', 'Summary', ondelete='cascade', 
        domain=[('state','=','completed')])
    total_task_time = fields.Float('Total Task Time')
    state = fields.Selection([('draft', 'Draft'),
                                ('waiting','Waiting For Approval'),
                                ('approved','Approved')                            
                                                ], default='draft', string='Status')
    
    
    # additional_details = fields.One2many('additional.task.details', 'task_summary_id', 'Additional Details')
    # @api.multi
    # def form_view(self):
    #     report_form =self.env.ref('Choice_org_addons.view_task_management_form').id
    #     print "\n\n____________report_form___________",report_form
    #     return {
    #        'type': 'ir.actions.act_window',
    #        'name': 'Task Mangement',
    #        'res_model': 'task.management',
    #        'view_mode': 'form',
    #        'view_type': 'form',
    #        'target': 'current',
    #        'views': [(report_form, 'form')],
    #        'context': {'create': False,'edit': True,'remove_uid_domain': True},
    #     }

    @api.multi
    def send_approval(self):
        self.state = 'waiting'
    
    def approve(self):
        for i in self:
            if i.reviewer_id.id == self._uid:
                i.state = 'approved'
            else:
                raise ValidationError(_("You cannot revert to this task summary."))

    @api.multi
    def mass_approval(self):
        a = []
        task_mark = False
        for i in self.task_summary:
            if i.task_approve_check == True:
                task_mark = True
                break
        print "\n\n______ALL APPROVED______",
        for i in self.task_summary:
            print "\n\n__________i__________",i,i.check
            if task_mark == True:
                if i.task_approve_check == True:
                    if (i.task_summary_id.reviewer_id.id == self._uid) or (self._uid == 1):
                        i.approval_status = 'approved'
                        self.state = 'approved'
                        print("approved")
                    else:
                        raise ValidationError(_("You donot have permission to approve this task."))
            else:
                if (i.task_summary_id.reviewer_id.id == self._uid) or (self._uid == 1):
                    i.approval_status = 'approved'
                    self.state = 'approved'
                    print("approved")
                else:
                    raise ValidationError(_("You donot have permission to approve this task."))
                
        #     print "\n\n_________i_______outside for________",i.approval_status
        #     print "\n\n_____________STATE_________________",self.state
        #     a.append(i.approval_status)
        # print "\n\n_________a__________",a
        # b=a[0:1]
        # for x in range (len(a)-1):
        #     print "\n\n__________a[x]___________",a[x],a[0]
        #     if a[0]== 'approved':
        #         if a[x] == a[x+1]:
        #             print "\n\n_______a[x]______a[x+1]___67__",a[x],a[x+1]
        #             self.state = 'approved'
        #         else:
        #             print "\n\n_______a[x]______a[x+1]__70___",a[x],a[x+1]
        #             self.state = 'draft'

        #     else:
        #         print "\n\n_______a[x]______a[x+1]__74___",a[x],a[x+1]
        #         self.state = 'draft'

    @api.multi
    def mass_rejection(self):
        print "\n\n _______ALL REJECTED____________"
        task_mark = False
        for i in self.task_summary:
            if i.task_approve_check == True:
                task_mark = True
                break

        for i in self.task_summary:
            if task_mark == True:
                if i.task_approve_check == True:
                    if (i.task_summary_id.reviewer_id.id == self._uid) or (self._uid == 1):
                        i.approval_status = 'reject'
                        self.state = 'draft'
                        i.task_reject = True
                    else:
                        raise ValidationError(_("You donot have permission to reject this task."))
            else:
                if (i.task_summary_id.reviewer_id.id == self._uid) or (self._uid == 1):
                    i.approval_status = 'reject'
                    self.state = 'draft'
                    i.task_reject = True
                else:
                    raise ValidationError(_("You donot have permission to reject this task."))

    @api.model
    def cron_approve_status(self):
        print "\n\n_________SCHEDULER TO REMOVE APPROVED TASK__________",self
        
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        result = super(TaskSummary, self).fields_view_get(view_id, view_type, toolbar=toolbar, submenu=submenu)
        print "context =================================",self._context
        return result

class AdditionalTaskDetails(models.Model):
    _name = 'additional.task.details'
    _description = 'Additional Task Details'
    
    date = fields.Date('Date')
    description = fields.Char('Description')
    hours_spent = fields.Float('Hours')
    task_summary_id = fields.Many2one('task.summary', 'Task Summary')
