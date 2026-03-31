from odoo import models, fields, api

class OpAttendanceSheet(models.Model):
    _inherit = 'op.attendance.sheet'

    sfera_calendar_id = fields.Many2one('sfera.calendar', string='Sfera Calendar Session')

class SferaCalendar(models.Model):
    _inherit = 'sfera.calendar'

    attendance_sheet_ids = fields.One2many('op.attendance.sheet', 'sfera_calendar_id', string='Attendance Sheets')

    def action_view_attendance(self):
        self.ensure_one()
        action = self.env.ref('openeducat_attendance.act_open_op_attendance_sheet_view').read()[0]
        action['domain'] = [('sfera_calendar_id', '=', self.id)]
        action['context'] = {
            'default_sfera_calendar_id': self.id,
            'default_batch_id': self.batch_id.id,
            'default_course_id': self.course_id.id,
            'default_faculty_id': self.faculty_id.id,
            'default_attendance_date': self.start_datetime.date() if self.start_datetime else fields.Date.today(),
        }
        return action
