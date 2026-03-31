from odoo import models, fields, api

class PublicHoliday(models.Model):
    _name = 'public.holiday'
    _description = 'Public Holidays'
    
    name = fields.Char('Bayram nomi', required=True)
    date = fields.Date('Sana', required=True)
    
    _sql_constraints = [
        ('date_unique', 'unique(date)', 'Bu sana uchun bayram allaqachon qo\'shilgan!')
    ]
