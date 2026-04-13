from odoo import models, fields, api, _
from datetime import datetime, timedelta

class OpStudent(models.Model):
    _inherit = 'op.student'
    _order = 'create_date desc'

    parent_name = fields.Char(string="Ota-onasining ismi")
    parent_phone = fields.Char(string="Ota-onasining raqami")
    batch_id = fields.Many2one('op.batch', string="Guruh")
    comment = fields.Text(string="Izohlar") 
    internal_comment = fields.Text(string="Ichki Izoh")

    @api.model_create_multi
    def create(self, vals_list):
        """ 1. Multi-create qo'llab-quvvatlash va vals_list bilan ishlash """
        for vals in vals_list:
            # Import paytida name bo'lmasa, familya va ismdan yasab olamiz
            if (not vals.get('name') or vals.get('name') == '/') and vals.get('first_name'):
                vals['name'] = f"{vals['first_name']} {vals.get('last_name') or ''}".strip()
            
            # Agar hali ham name bo'lmasa (res_partner_check_name xatosini oldini olish)
            if not vals.get('name'):
                vals['name'] = "Yangi Talaba"

        records = super(OpStudent, self).create(vals_list)
        
        # Har bir yaratilgan record va unga mos vals'ni tekshiramiz
        for rec, vals in zip(records, vals_list):
            if vals.get('internal_comment'):
                rec._create_task_from_comment(vals['internal_comment'])
            
            # Batch berilgan bo'lsa, avtomatik kursga yozish
            if vals.get('batch_id'):
                rec._sync_student_course(vals['batch_id'])

        return records

    def write(self, vals):
        """ 2. Write metodida self (recordset) ichidagi har bir record uchun ishlash """
        # Agar ism o'zgarsa lekin name kelmasa (first_name/last_name o'zgarganda)
        if 'first_name' in vals or 'last_name' in vals:
            for rec in self:
                fname = vals.get('first_name', rec.first_name)
                lname = vals.get('last_name', rec.last_name)
                if not vals.get('name'):
                    vals['name'] = f"{fname or ''} {lname or ''}".strip()

        res = super(OpStudent, self).write(vals)
        
        if 'internal_comment' in vals:
            for rec in self:
                rec._create_task_from_comment(vals['internal_comment'])
        
        if 'batch_id' in vals:
            for rec in self:
                rec._sync_student_course(vals['batch_id'])
                
        return res

    def _sync_student_course(self, batch_id):
        """ Talabani guruhga avtomatik biriktirish """
        self.ensure_one()
        batch = self.env['op.batch'].browse(batch_id)
        if not batch:
            return

        # Tekshiramiz, bu guruhda allaqachon bormi?
        existing_course = self.env['op.student.course'].search([
            ('student_id', '=', self.id),
            ('batch_id', '=', batch.id)
        ], limit=1)

        if not existing_course:
            self.env['op.student.course'].create({
                'student_id': self.id,
                'batch_id': batch.id,
                'course_id': batch.course_id.id,
                'state': 'running',
            })

    def _create_task_from_comment(self, comment):
        """ 3. Activity yaratish mantiqini optimallashtirish """
        if not comment:
            return
            
        comment_lower = comment.lower()
        # 'chorshanba' va '10' borligini tekshirish
        if "chorshanba" in comment_lower and "10" in comment_lower:
            today = datetime.now()
            # Chorshanbagacha bo'lgan kunlar (2 - chorshanba indeksi)
            days_ahead = 2 - today.weekday()
            if days_ahead <= 0: 
                days_ahead += 7
            
            target_date = today + timedelta(days=days_ahead)
            
            # Activity yaratish - model ID'sini keshdan olish uchun _get_id ishlatamiz
            model_id = self.env['ir.model']._get_id('op.student')
            
            # Activity turini xavfsizroq olish (xml_id bo'lmasa xato bermasligi uchun)
            activity_type = self.env.ref('mail.mail_activity_data_call', raise_if_not_found=False)
            activity_type_id = activity_type.id if activity_type else False

            self.env['mail.activity'].create({
                'res_id': self.id,
                'res_model_id': model_id,
                'activity_type_id': activity_type_id,
                'summary': _("Qayta qo'ng'iroq (Avtomatik)"),
                'note': comment,
                'date_deadline': target_date.date(),
                'user_id': self.env.uid, # Joriy foydalanuvchi
            })