from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from datetime import date, timedelta
import logging

_logger = logging.getLogger(__name__)

# Qaysi stage ga o'tsa qanday activity qo'shiladi
STAGE_ACTIVITY_MAP = {
    'Sifatli Qilindi': {
        'summary': 'Qayta qo\'ng\'iroq qilish kerak',
        'note': '1 kundan keyin talabaga qayta qo\'ng\'iroq qiling va holatini aniqlang.',
        'days': 1,
    },
    'O\'quv Markazga kelaman dedi': {
        'summary': 'O\'quv markazga kelishini tasdiqlash',
        'note': 'Talaba o\'quv markazga kelaman dedi. 1 kundan keyin qayta qo\'ng\'iroq qilib tasdiqlang.',
        'days': 1,
    },
}

class CrmLead(models.Model):
    _inherit = "crm.lead"

    first_name = fields.Char(string="Ism", required=True)
    last_name = fields.Char(string="Familiya")
    student_phone = fields.Char(string="Talaba telefoni", required=True)
    parent_phone = fields.Char(string="Ota-ona telefoni")
    parent_name = fields.Char(string="Ota-onasini ismi")
    age = fields.Integer(string="Yoshi", default=15)
    course_id = fields.Many2one("op.course", string="Kurs")
    admission_id = fields.Many2one("op.admission.register", string="Admission")
    address = fields.Char(string="Manzil")
    batch_id = fields.Many2one("op.batch", string="Guruh")
    student_id = fields.Many2one("op.student", string="Talaba")
    lead_source = fields.Selection([
        ('instagram', 'Instagram'),
        ('telegram', 'Telegram'),
        ('tavsiya', 'Tavsiya'),
        ('banner', 'Banner'),
        ('other', 'Boshqa'),
    ], string="Qayerdan keldi", default='other')
    lead_count_compute = fields.Integer(string="Lead Soni", compute="_compute_lead_count", store=True)

    @api.depends('first_name') # Har doim 1 bo'lishi uchun
    def _compute_lead_count(self):
        for record in self:
            record.lead_count_compute = 1

    @api.onchange('first_name', 'last_name')
    def _onchange_student_name(self):
        if self.first_name:
            self.name = f"{self.first_name} {self.last_name or ''}"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'first_name' in vals and not vals.get('name'):
                vals['name'] = f"{vals['first_name']} {vals.get('last_name') or ''}"
            # Yosh validatsiyasidan o'tish uchun (rasmdagi xatolikka qarshi)
            if 'age' in vals and (not vals.get('age') or vals.get('age') < 3):
                vals['age'] = 15

        records = super(CrmLead, self).create(vals_list)
        
        for record in records:
            # Har doim Application yaratishga harakat qilamiz
            record._auto_create_application()
            
        return records

    def _auto_create_application(self):
        """ Lead uchun Application (op.admission) yaratish """
        for record in self:
            register = record.admission_id
            if not register and record.course_id:
                # Kursga mos keluvchi ochiq registerni qidirish
                register = self.env['op.admission.register'].sudo().search([
                    ('course_id', '=', record.course_id.id),
                    ('state', 'in', ['application', 'admission'])
                ], limit=1)

            if register:
                Model = self.env.get('op.admission') or self.env.get('op.application')
                if Model is not None:
                    safe_age = record.age if record.age >= 3 else 15
                    calc_date = date.today() - relativedelta(years=safe_age)
                    
                    app_vals = {
                        'name': f"{record.first_name} {record.last_name or ''}",
                        'first_name': record.first_name,
                        'last_name': record.last_name,
                        'course_id': record.course_id.id if record.course_id else register.course_id.id,
                        'register_id': register.id,
                        'mobile': record.student_phone,
                        'street': record.address,
                        'gender': 'm',
                        'birth_date': calc_date,
                    }
                    
                    # To'lov sharti (fees term)
                    term = self.env['op.fees.terms'].sudo().search([], limit=1)
                    if term:
                        app_vals['fees_term_id'] = term.id

                    Model.sudo().create(app_vals)
                    _logger.debug("Application yaratildi: %s", record.name)

    def write(self, vals):
        """
        Stage o'zgarganda:
        1. Avtomatik activity (task) yaratish
        2. 'Sifatli Qilindi' stagega o'tganda barcha maydonlarni tekshirish
        3. 'Kursga yozildi' stagega o'tganda ota-ona avtomatik yaratish
        """
        from odoo.exceptions import ValidationError

        # Avval eski stage_id ni saqlab olamiz
        old_stage_map = {}
        if 'stage_id' in vals:
            for lead in self:
                old_stage_map[lead.id] = lead.stage_id.id

        # ─── 'Sifatli Qilindi' stagega o'tganda validatsiya ───
        if 'stage_id' in vals:
            new_stage = self.env['crm.stage'].browse(vals['stage_id'])
            if new_stage.name == 'Sifatli Qilindi':
                for lead in self:
                    if old_stage_map.get(lead.id) != vals['stage_id']:
                        missing = []
                        if not lead.age or lead.age < 3:
                            missing.append("Yoshi")
                        if not lead.course_id:
                            missing.append("Kurs")
                        if not lead.lead_source:
                            missing.append("Qayerdan keldi")
                        if not lead.parent_name:
                            missing.append("Vasiy ismi")
                        if not lead.parent_phone:
                            missing.append("Vasiy telefoni")
                        if not lead.address:
                            missing.append("Manzil")
                        if missing:
                            raise ValidationError(
                                "Sifatli Qilindi stagega o'tish uchun quyidagi maydonlarni to'ldiring:\n• "
                                + "\n• ".join(missing)
                            )

        result = super(CrmLead, self).write(vals)

        # Agar stage o'zgargan bo'lsa
        if 'stage_id' in vals:
            new_stage = self.env['crm.stage'].browse(vals['stage_id'])
            stage_name = new_stage.name if new_stage else ''

            # ─── Avtomatik activity yaratish (mavjud kod) ───
            if stage_name in STAGE_ACTIVITY_MAP:
                config = STAGE_ACTIVITY_MAP[stage_name]
                deadline = fields.Date.context_today(self) + timedelta(days=config['days'])

                for lead in self:
                    if old_stage_map.get(lead.id) != vals['stage_id']:
                        lead.activity_schedule(
                            'mail.mail_activity_data_todo',
                            date_deadline=deadline,
                            summary=config['summary'],
                            note=config['note'],
                            user_id=self.env.uid,
                        )

            # 'Kursga yozildi' stagega o'tganda parent yaratish
            # wizard (Guruhga qo'shish) orqali student yaratilganda avtomatik bo'ladi.

        return result

