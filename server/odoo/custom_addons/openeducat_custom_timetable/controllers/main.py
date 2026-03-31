from odoo import http, fields
from odoo.http import request
from datetime import datetime, time

class TeacherPortal(http.Controller):

    @http.route(['/teacher/panel'], type='http', auth="user", website=True)
    def teacher_dashboard(self, **kwargs):
        user = request.env.user
        
        # Admin yoki test holatlarida turli profil dublikatlari yaratilgan bo'lishi mumkinligi uchun qidiruvni kengaytiramiz:
        # 1. Partner orqali (eng ishonchli usul)
        # 2. To'g'ridan to'g'ri ism orqali yoki email orqali izlash
        faculties = request.env['op.faculty'].sudo().search([
            '|', '|',
            ('partner_id', '=', user.partner_id.id),
            ('partner_id.name', '=', user.partner_id.name),
            ('name', '=', user.name)
        ])
        
        import pytz
        from datetime import datetime, time, timedelta

        today = fields.Date.today()
        # Odoo ma'lumotlar bazasida UTC saqlanadi, shuning uchun mahalliy vaqttan UTC ga o'giramiz
        user_tz = pytz.timezone(request.env.user.tz or 'UTC')
        local_start = user_tz.localize(datetime.combine(today, time.min))
        local_end = user_tz.localize(datetime.combine(today, time.max))
        
        start_of_day = local_start.astimezone(pytz.utc).replace(tzinfo=None)
        end_of_day = local_end.astimezone(pytz.utc).replace(tzinfo=None)

        if faculties:
            sessions = request.env['sfera.calendar'].sudo().search([
                ('faculty_id', 'in', faculties.ids),
                ('start_datetime', '>=', start_of_day),
                ('start_datetime', '<=', end_of_day)
            ])
            
            # Qo'shimcha xavfsizlik va debugging uchun, agar sessions topilmasa va barcha sessionlarni chiqarishni sinash uchun
            # sessions = request.env['sfera.calendar'].sudo().search([('start_datetime', '>=', start_of_day), ('start_datetime', '<=', end_of_day)])
        else:
            sessions = []

        return request.render('openeducat_custom_timetable.teacher_dashboard_template', {
            'user': user,
            'faculty': faculties[0] if faculties else False,
            'sessions': sessions,
        })

    @http.route(['/teacher/session/<int:session_id>/attendance'], type='http', auth="user", website=True)
    def session_attendance(self, session_id, **kwargs):
        # 1. Sfera calendar session ni sudo bilan topamiz
        session = request.env['sfera.calendar'].sudo().browse(session_id)
        if not session.exists():
            return "Session topilmadi!"

        # 2. Mavjud sheetni qidiramiz
        attendance_sheet = request.env['op.attendance.sheet'].sudo().search([
            ('sfera_calendar_id', '=', session.id)
        ], limit=1)

        # 3. Agar sheet bo'lmasa, yaratamiz
        if not attendance_sheet:
            try:
                # OpenEduCat-da 'register_id' majburiy bo'lishi mumkin. 
                # Agar kursda register bo'lsa shuni olamiz, bo'lmasa False.
                register = request.env['op.attendance.register'].sudo().search([('course_id', '=', session.course_id.id)], limit=1)
                if not register:
                    register = request.env['op.attendance.register'].sudo().search([], limit=1)
                
                attendance_sheet = request.env['op.attendance.sheet'].sudo().create({
                    'register_id': register.id if register else False,
                    'sfera_calendar_id': session.id,
                    # Fallback op.session_id uchun bo'sh qoldirish mumkin yoyoki majburiy bo'lsa xato berishi mumkin
                    'name': session.name or "Attendance",
                    'faculty_id': session.faculty_id.id,
                    'course_id': session.course_id.id,
                    'batch_id': session.batch_id.id,
                    'attendance_date': session.start_datetime.date() if session.start_datetime else fields.Date.today(),
                })
            except Exception as e:
                return f"Attendance Sheet yaratishda xato: {str(e)}"

        # 4. Odoo 19 formatida backendga redirect
        redirect_url = f"/odoo/action-openeducat_attendance.act_open_op_attendance_sheet_view/{attendance_sheet.id}"
        
        return request.redirect(redirect_url)

    @http.route(['/teacher/exams'], type='http', auth="user", website=True)
    def teacher_exams_redirect(self, **kwargs):
        # Backenddagi Exams (Imtihonlar) oynasiga to'g'ridan-to'g'ri redirect
        return request.redirect("/odoo/action-openeducat_exam.act_open_op_exam_view")