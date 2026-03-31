from odoo import models, fields

class OpStudent(models.Model):
    _inherit = 'op.student'

    # Talabaga bitta guruhni biriktirish uchun field
    batch_id = fields.Many2one('op.batch', string='Guruh (Batch)')