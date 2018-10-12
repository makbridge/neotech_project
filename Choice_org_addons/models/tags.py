from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError

class TagsConfig(models.Model):
    _name = 'tags.config'
    _description = 'Tags Config'
    
    name = fields.Char(string="Name")
    
