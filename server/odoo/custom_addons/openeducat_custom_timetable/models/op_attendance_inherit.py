from odoo import models, fields, api

class OpAttendanceSheet(models.Model):
    _inherit = 'op.attendance.sheet'

    def attendance_start(self):
        # 1. Statusni o'zgartirish: Odoo'da tugma bosilganda state o'zgarishi 
        # odatda avtomatik bo'ladi, lekin biz xatolik bermasligi uchun 
        # mavjud statuslarni tekshirib o'zgartiramiz.
        for sheet in self:
            # Agar 'attendance_start' xato bersa, 'start' variantini sinaymiz
            try:
                sheet.state = 'attendance_start'
            except:
                sheet.state = 'start'

            # 2. Talabalarni yuklash (Batch orqali)
            #
            if not sheet.attendance_line:
                students = self.env['op.student'].search([('batch_id', '=', sheet.batch_id.id)])
                
                attendance_lines = []
                for student in students:
                    attendance_lines.append((0, 0, {
                        'student_id': student.id,
                        'present': True,
                    }))
                
                if attendance_lines:
                    sheet.write({'attendance_line': attendance_lines})
        
        return True