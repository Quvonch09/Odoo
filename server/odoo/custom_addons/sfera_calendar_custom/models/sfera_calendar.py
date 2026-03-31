from odoo import models, fields, api

class SferaCalendar(models.Model):
    _name = 'sfera.calendar'
    _description = 'Sfera Lesson Calendar'
    _inherit = ['mail.thread']

    name = fields.Char('Name', compute='_compute_name', store=True)
    batch_id = fields.Many2one('op.batch', 'Batch', required=True)
    course_id = fields.Many2one('op.course', 'Course', required=True)
    lesson_id = fields.Many2one('op.lesson', 'Lesson')
    faculty_id = fields.Many2one('op.faculty', 'Faculty', required=True)
    classroom_id = fields.Many2one('op.classroom', 'Classroom')
    start_datetime = fields.Datetime('Start Time', required=True)
    end_datetime = fields.Datetime('End Time', required=True)
    color = fields.Integer('Color Index', default=0)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('done', 'Done'),
        ('cancel', 'Canceled')
    ], string='Status', default='draft', tracking=True)

    @api.depends('batch_id', 'lesson_id', 'start_datetime')
    def _compute_name(self):
        for rec in self:
            name = rec.batch_id.name or 'New'
            if rec.lesson_id:
                name += f" - {rec.lesson_id.name}"
            if rec.start_datetime:
                name += f" ({rec.start_datetime.strftime('%Y-%m-%d %H:%M')})"
            rec.name = name

    def action_confirm(self):
        self.state = 'confirm'

    def action_done(self):
        self.state = 'done'

    def action_draft(self):
        self.state = 'draft'

    def action_cancel(self):
        self.state = 'cancel'
