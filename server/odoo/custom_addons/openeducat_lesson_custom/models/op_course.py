from odoo import models, fields

class OpCourse(models.Model):
    _inherit = 'op.course'

    lesson_ids = fields.One2many('op.lesson', 'course_id', string='Lessons')
