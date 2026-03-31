from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import timedelta
import datetime

class OpBatch(models.Model):
    _inherit = 'op.batch'

    faculty_id = fields.Many2one('op.faculty', string='Mentor (Faculty)', required=True)
    # Yangi maydon: Xona (Classroom)
    classroom_id = fields.Many2one('op.classroom', string='Darsxonasi', required=True)
    
    start_time = fields.Float(string='Dars boshlanishi', required=True, default=9.0)
    end_time = fields.Float(string='Dars tugashi', required=True, default=11.0)
    
    day_type = fields.Selection([
        ('odd', 'Toq kunlar (Dush-Chor-Jum)'),
        ('even', 'Juft kunlar (Sesh-Pay-Shan)'),
        ('daily', 'Har kuni')
    ], string='Dars kunlari', required=True, default='odd')
    
    course_end_date = fields.Date(string='Kurs tugash sanasi', required=True)

    def generate_timetable_button(self):
        model_name = 'sfera.calendar'
        timetable_obj = self.env[model_name]
        
        days_lookup = {
            'odd': [0, 2, 4],
            'even': [1, 3, 5],
            'daily': [0, 1, 2, 3, 4, 5]
        }
        
        selected_days = days_lookup.get(self.day_type)
        current_date = self.start_date
        
        if not current_date or not self.course_end_date:
            raise UserError("Sanalarni to'ldiring!")

        # Kurs darslarini sequence bo'yicha olish
        lessons = self.env['op.lesson'].search([
            ('course_id', '=', self.course_id.id)
        ], order='sequence, id')
        
        lesson_index = 0
        total_lessons = len(lessons)

        # Bayram kunlarini olish
        holiday_dates = self.env['public.holiday'].search([]).mapped('date')
        
        while current_date <= self.course_end_date:
            # Dars kuni bo'lsa VA bayram bo'lmasa
            if current_date.weekday() in selected_days and current_date not in holiday_dates:
                # Agar darslar tugagan bo'lsa to'xtash
                if lesson_index >= total_lessons:
                    break
                    
                # O'zbekiston vaqti UTC+5
                start_dt = datetime.datetime.combine(current_date, datetime.time()) + timedelta(hours=self.start_time - 5)
                end_dt = datetime.datetime.combine(current_date, datetime.time()) + timedelta(hours=self.end_time - 5)
                
                # Mavjud darsni tekshirish
                existing_session = timetable_obj.search([
                    ('batch_id', '=', self.id),
                    ('start_datetime', '=', start_dt)
                ], limit=1)
                
                if not existing_session:
                    # Keyingi darsni tanlash
                    lesson = lessons[lesson_index] if lesson_index < total_lessons else False
                    
                    timetable_obj.create({
                        'batch_id': self.id,
                        'course_id': self.course_id.id,
                        'lesson_id': lesson.id if lesson else False,
                        'faculty_id': self.faculty_id.id,
                        'classroom_id': self.classroom_id.id,
                        'start_datetime': start_dt,
                        'end_datetime': end_dt,
                        'state': 'draft',
                    })
                    # Lesson indexni oshirish
                    if lesson:
                        lesson_index += 1
            
            current_date += timedelta(days=1)
        
        return {
            'name': 'Dars jadvali',
            'type': 'ir.actions.act_window',
            'res_model': model_name,
            'view_mode': 'calendar,list,form',
            'domain': [('batch_id', '=', self.id)],
            'target': 'current',
        }