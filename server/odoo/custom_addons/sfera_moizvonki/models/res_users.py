from odoo import models, fields

class MoizvonkiEmployee(models.Model):
    _name = 'moizvonki.employee'
    _description = 'Moi Zvonki Employee Mapping'

    user_id = fields.Many2one('res.users', string='Odoo Foydalanuvchi', required=True)
    moizvonki_id = fields.Char(string='Moi Zvonki ID', required=True)
