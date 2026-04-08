from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import timedelta, datetime, time
import pytz

class OpBatch(models.Model):
    _inherit = 'op.batch'

    # Sfera Custom Schedule Fields (Manual Input)
    sfera_start_time = fields.Char(string='Dars boshlanishi (masalan, 09:00)', default='09:00', help="Format: HH:MM")
    sfera_end_time = fields.Char(string='Dars tugashi (masalan, 11:00)', default='11:00', help="Format: HH:MM")
    
    sfera_day_type = fields.Selection([
        ('TOQ_KUNLAR', 'Toq kunlar (Du-Chor-Ju)'),
        ('JUFT_KUNLAR', 'Juft kunlar (Se-Pay-Sha)'),
        ('HAR_KUNI', 'Har kuni')
    ], string='Dars kunlari', default='TOQ_KUNLAR')
    
    sfera_faculty_id = fields.Many2one('op.faculty', string='Mentor (O\'qituvchi)')
    sfera_classroom_id = fields.Many2one('op.classroom', string='Xona (Room)')
    sfera_subject_id = fields.Many2one('op.subject', string='Fan (Subject)')
    sfera_end_date = fields.Date(string='Kurs tugash sanasi')

    def generate_timetable_manual(self):
        """
        Guruh uchun dars jadvalini qo'lda kiritilgan malumotlar asosida shakllantirish.
        Endi standart op.session modelidan foydalanadi.
        """
        self.ensure_one()
        session_obj = self.env['op.session']
        
        # Tekshiruvlar
        if not self.sfera_start_time or not self.sfera_end_time:
            raise UserError("Boshlanish va tugash vaqtlarini kiriting!")
        if not self.sfera_end_date:
            raise UserError("Kurs tugash sanasini kiriting!")
        if not self.start_date:
            raise UserError("Guruh boshlanish sanasini kiriting!")
        
        # Subjectid tekshirish
        subject_id = self.sfera_subject_id.id
        if not subject_id:
            # Agar tanlanmagan bo'lsa, kursdagi birinchi fanni olishga urinish
            if self.course_id.subject_ids:
                subject_id = self.course_id.subject_ids[0].id
            else:
                raise UserError("Iltimos, fanni (Subject) tanlang yoki kursga fanlarni biriktiring.")

        try:
            h1, m1 = map(int, self.sfera_start_time.split(':'))
            h2, m2 = map(int, self.sfera_end_time.split(':'))
        except:
            raise UserError("Vaqt formati noto'g'ri! Iltimos, HH:MM formatida kiriting (masalan: 09:00)")

        days_lookup = {
            'TOQ_KUNLAR': [0, 2, 4], # Mon, Wed, Fri
            'JUFT_KUNLAR': [1, 3, 5], # Tue, Thu, Sat
            'HAR_KUNI': [0, 1, 2, 3, 4, 5] # Mon-Sat
        }
        
        selected_days = days_lookup.get(self.sfera_day_type)
        current_date = self.start_date
        
        # O'zbekiston vaqti (UTC+5)
        # Odoo serverda UTC saqlaydi
        
        holiday_dates = self.env['public.holiday'].search([]).mapped('date')
        
        created_count = 0
        while current_date <= self.sfera_end_date:
            if current_date.weekday() in selected_days and current_date not in holiday_dates:
                
                start_dt = datetime.combine(current_date, time(h1, m1)) - timedelta(hours=5)
                end_dt = datetime.combine(current_date, time(h2, m2)) - timedelta(hours=5)

                # Mavjud op.session ni tekshirish
                existing_session = session_obj.search([
                    ('batch_id', '=', self.id),
                    ('start_datetime', '=', start_dt)
                ], limit=1)
                
                if not existing_session:
                    session_obj.create({
                        'batch_id': self.id,
                        'course_id': self.course_id.id,
                        'subject_id': subject_id,
                        'faculty_id': self.sfera_faculty_id.id or (self.faculty_id.id if 'faculty_id' in self._fields else False),
                        'classroom_id': self.sfera_classroom_id.id or (self.classroom_id.id if 'classroom_id' in self._fields else False),
                        'start_datetime': start_dt,
                        'end_datetime': end_dt,
                        'state': 'draft',
                    })
                    created_count += 1
            
            current_date += timedelta(days=1)
        
        if created_count == 0:
            raise UserError("Ushbu sanalar oralig'ida yangi darslar yaratilmadi.")

        return {
            'effect': {
                'fadeout': 'slow',
                'message': f'Muvaffaqiyatli! {created_count} ta standart sessiya yaratildi.',
                'type': 'rainbow_man',
            }
        }