from odoo import models, fields, api

class OpLesson(models.Model):
    _name = 'op.lesson'
    _description = 'OpenEduCat Lesson'
    _order = 'sequence, id'

    name = fields.Char('Lesson Name', required=True)
    course_id = fields.Many2one('op.course', 'Course', required=True, ondelete='cascade')
    sequence = fields.Integer('Sequence', default=10)
    description = fields.Html('Description')

    @api.model
    def get_import_templates(self):
        return [{
            'label': ('Import Template for Lesson Plans'),
            'template': '/openeducat_lesson_custom/static/xls/op_lesson.xls'
        }]
