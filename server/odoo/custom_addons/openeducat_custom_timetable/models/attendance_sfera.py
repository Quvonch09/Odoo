from odoo import models, fields, api

class OpAttendanceLine(models.Model):
    _inherit = 'op.attendance.line'

    sfera_status = fields.Selection([
        ('present', 'Keldi'),
        ('absent', 'Kelmadi'),
        ('excused', 'Sababli')
    ], string='Sfera Status')

    @api.onchange('sfera_status')
    def _onchange_sfera_status(self):
        if self.sfera_status == 'present':
            self.present = True
            self.absent = False
            self.excused = False
            self.late = False
        elif self.sfera_status == 'absent':
            self.present = False
            self.absent = True
            self.excused = False
            self.late = False
        elif self.sfera_status == 'excused':
            self.present = False
            self.absent = False
            self.excused = True
            self.late = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'sfera_status' in vals:
                status = vals['sfera_status']
                if status == 'present':
                    vals.update({'present': True, 'absent': False, 'excused': False, 'late': False})
                elif status == 'absent':
                    vals.update({'present': False, 'absent': True, 'excused': False, 'late': False})
                elif status == 'excused':
                    vals.update({'present': False, 'absent': False, 'excused': True, 'late': False})
        return super().create(vals_list)

    def write(self, vals):
        if 'sfera_status' in vals:
            status = vals['sfera_status']
            if status == 'present':
                vals.update({'present': True, 'absent': False, 'excused': False, 'late': False})
            elif status == 'absent':
                vals.update({'present': False, 'absent': True, 'excused': False, 'late': False})
            elif status == 'excused':
                vals.update({'present': False, 'absent': False, 'excused': True, 'late': False})
        return super().write(vals)

class OpBatch(models.Model):
    _inherit = 'op.batch'

    def action_sfera_attendance(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'sfera_attendance_dashboard',
            'name': f'Davomat - {self.name}',
            'context': {
                'active_id': self.id,
                'batch_id': self.id,
                'batch_name': self.name,
            }
        }

    @api.model
    def get_attendance_data(self, batch_id, month=None, year=None):
        batch = self.browse(batch_id)
        if not month or not year:
            today = fields.Date.today()
            month, year = today.month, today.year
        
        # Get sessions (op.session) for the month
        start_date = fields.Date.to_date(f'{year}-{month}-01')
        import calendar as py_calendar
        last_day = py_calendar.monthrange(year, month)[1]
        end_date = fields.Date.to_date(f'{year}-{month}-{last_day}')
        
        # Search in op.session instead of sfera.calendar
        sessions = self.env['op.session'].search([
            ('batch_id', '=', batch_id),
            ('start_datetime', '>=', start_date),
            ('start_datetime', '<=', end_date)
        ], order='start_datetime asc')
        
        # Get active students in batch
        student_courses = self.env['op.student.course'].search([
            ('batch_id', '=', batch_id),
            ('state', '=', 'running')
        ])
        students = student_courses.mapped('student_id')
        
        # Search attendance lines linked to these sessions
        attendance_lines = self.env['op.attendance.line'].search([
            ('attendance_id.session_id', 'in', sessions.ids),
            ('student_id', 'in', students.ids)
        ])
        
        att_map = {}
        for line in attendance_lines:
            sid = line.student_id.id
            cid = line.attendance_id.session_id.id
            if sid not in att_map: att_map[sid] = {}
            
            status = line.sfera_status
            if not status:
                if line.absent: status = 'absent'
                elif line.excused: status = 'excused'
                elif line.present and line.attendance_id.state == 'done': status = 'present'
                else: status = 'none'

            att_map[sid][cid] = {
                'id': line.id,
                'status': status,
                'remark': line.remark or ''
            }

        return {
            'students': [{'id': s.id, 'name': s.name} for s in students],
            'sessions': [{
                'id': s.id, 
                'date': s.start_datetime.strftime('%Y-%m-%d'),
                'day': s.start_datetime.day,
                'lesson': s.subject_id.name or ''
            } for s in sessions],
            'attendance': att_map,
            'batch_name': batch.name,
        }

    @api.model
    def set_attendance_status(self, batch_id, student_id, session_id, status, remark=''):
        # session_id here refers to op.session
        session = self.env['op.session'].browse(session_id)
        
        sheet = self.env['op.attendance.sheet'].sudo().search([
            ('session_id', '=', session_id)
        ], limit=1)
        
        if not sheet:
            register = self.env['op.attendance.register'].sudo().search([
                ('batch_id', '=', batch_id)
            ], limit=1)
            if not register:
                register = self.env['op.attendance.register'].sudo().create({
                    'name': f'Register - {session.batch_id.name}',
                    'course_id': session.course_id.id,
                    'batch_id': session.batch_id.id,
                })
            
            sheet = self.env['op.attendance.sheet'].sudo().create({
                'register_id': register.id,
                'session_id': session_id,
                'attendance_date': session.start_datetime.date(),
                'faculty_id': session.faculty_id.id,
                'state': 'start',
            })

        line = self.env['op.attendance.line'].sudo().search([
            ('attendance_id', '=', sheet.id),
            ('student_id', '=', student_id)
        ], limit=1)
        
        vals = {
            'sfera_status': status,
            'remark': remark,
        }
        
        if line:
            line.write(vals)
        else:
            if student_id > 0: # 0 check for initialization
                vals.update({
                    'attendance_id': sheet.id,
                    'student_id': student_id,
                })
                self.env['op.attendance.line'].sudo().create(vals)
            
        return True
