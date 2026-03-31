from odoo import models, fields, api, _
from datetime import datetime, timedelta

class OpStudent(models.Model):
    _inherit = 'op.student'
    _order = 'create_date desc'

    parent_name = fields.Char(string="Ota-onasining ismi")
    parent_phone = fields.Char(string="Ota-onasining raqami")
    comment = fields.Text(string="Izohlar") 
    internal_comment = fields.Text(string="Ichki Izoh")

    @api.model_create_multi
    def create(self, vals_list):
        """ 1. Multi-create qo'llab-quvvatlash va vals_list bilan ishlash """
        records = super(OpStudent, self).create(vals_list)
        
        # Har bir yaratilgan record va unga mos vals'ni tekshiramiz
        for rec, vals in zip(records, vals_list):
            if vals.get('internal_comment'):
                rec._create_task_from_comment(vals['internal_comment'])
        return records

    def write(self, vals):
        """ 2. Write metodida self (recordset) ichidagi har bir record uchun ishlash """
        res = super(OpStudent, self).write(vals)
        if 'internal_comment' in vals:
            for rec in self:
                rec._create_task_from_comment(vals['internal_comment'])
        return res

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