from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError

class CheckList(models.Model):
    _name = 'check.list'
    _description = 'Check list'
    
    name = fields.Char(string='Description', required="True")
    state = fields.Selection([
                                ('todo', 'To-Do'),
                                ('done', 'Done'),
                                ('cancel', 'Cancel'),
                                ],default='todo', string='Status')
    task_id = fields.Many2one('task.management',string='Task Management')
    user_id = fields.Many2one('res.users',default=lambda self: self.env.user)
    
    @api.multi
    def done(self):
        self.state = 'done'
    
    @api.multi
    def cancel(self):
        self.state = 'cancel'
    
    @api.multi
    def todo(self):
        self.state = 'todo'
    

