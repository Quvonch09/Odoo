from odoo import models, fields, api

class SferaCalendar(models.Model):
    _name = 'sfera.calendar'
    _description = 'Sfera Lesson Calendar'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_datetime desc'

    name = fields.Char('Name', compute='_compute_name', store=True)
    batch_id = fields.Many2one('op.batch', 'Batch', required=True, tracking=True)
    course_id = fields.Many2one('op.course', 'Course', required=True, tracking=True)
    lesson_id = fields.Many2one('op.lesson', 'Lesson', tracking=True)
    faculty_id = fields.Many2one('op.faculty', 'Faculty', required=True, tracking=True)
    classroom_id = fields.Many2one('op.classroom', 'Classroom', tracking=True)
    start_datetime = fields.Datetime('Start Time', required=True, tracking=True)
    end_datetime = fields.Datetime('End Time', required=True, tracking=True)
    color = fields.Integer('Color Index', default=0)
    
    # Link to standard OpenEduCat models
    op_session_id = fields.Many2one('op.session', 'OpenEduCat Session')
    attendance_sheet_id = fields.Many2one('op.attendance.sheet', compute='_compute_attendance_sheet', string='Attendance Sheet')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('done', 'Done'),
        ('cancel', 'Canceled')
    ], string='Status', default='draft', tracking=True)

    def _compute_attendance_sheet(self):
        for rec in self:
            sheet = self.env['op.attendance.sheet'].search([('sfera_calendar_id', '=', rec.id)], limit=1)
            rec.attendance_sheet_id = sheet

    @api.depends('batch_id', 'lesson_id', 'start_datetime')
    def _compute_name(self):
        for rec in self:
            name = rec.batch_id.name or 'New'
            if rec.lesson_id:
                name += f" - {rec.lesson_id.name}"
            if rec.start_datetime:
                # O'zbekiston vaqti bilan ko'rsatish (UTC+5)
                from datetime import timedelta
                local_dt = rec.start_datetime + timedelta(hours=5)
                name += f" ({local_dt.strftime('%d.%m %H:%M')})"
            rec.name = name

    def action_confirm(self):
        self.state = 'confirm'

    def action_done(self):
        self.state = 'done'

    def action_draft(self):
        self.state = 'draft'

    def action_cancel(self):
        self.state = 'cancel'

    def action_view_attendance(self):
        self.ensure_one()
        sheet = self.env['op.attendance.sheet'].search([('sfera_calendar_id', '=', self.id)], limit=1)
        if not sheet:
            # Create sheet if not exists (using previous logic)
            self.env['op.batch'].set_attendance_status(self.batch_id.id, 0, self.id, 'none')
            sheet = self.env['op.attendance.sheet'].search([('sfera_calendar_id', '=', self.id)], limit=1)
            
        return {
            'name': 'Davomat varaqa',
            'type': 'ir.actions.act_window',
            'res_model': 'op.attendance.sheet',
            'view_mode': 'form',
            'res_id': sheet.id,
            'target': 'current',
        }
