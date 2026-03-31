from odoo import models, fields, api, _

class OpAdmissionRegister(models.Model):
    _inherit = 'op.admission.register'

    custom_fees = fields.Float(string='Course Fees Amount')
    min_count = fields.Integer(default=1) # Validation Error bermasligi uchun

    def action_quick_confirm(self):
        """Bu metod XML dagi Confirm tugmasi uchun shart"""
        for record in self:
            record.state = 'admission'
        return True

    def action_create_new_lead(self):
        self.ensure_one()
        return {
            'name': _('Yangi Ariza'),
            'type': 'ir.actions.act_window',
            'res_model': 'op.admission',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_register_id': self.id,
                'default_course_id': self.course_id.id,
                'default_fees': self.custom_fees, # Kontekst orqali narx
            }
        }

class OpAdmission(models.Model):
    _inherit = 'op.admission'

    # 1. Standart metodlarni 'override' qilib, narxni biz bergan qiymatda ushlab qolamiz
    @api.onchange('register_id', 'course_id')
    def onchange_register_course_fees(self):
        # Agar registerda narx bo'lsa, u standart mantiqni o'ldirib, o'zimiznikini qo'yadi
        if self.register_id and self.register_id.custom_fees > 0:
            self.fees = self.register_id.custom_fees

    # 2. Bazaga saqlashda yana bir bor tekshirish (Kafolat uchun)
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('register_id') and not vals.get('fees'):
                reg = self.env['op.admission.register'].browse(vals['register_id'])
                if reg.custom_fees:
                    vals['fees'] = reg.custom_fees
        
        records = super(OpAdmission, self).create(vals_list)
        
        # Max count kamaytirish
        for record in records:
            if record.register_id and record.register_id.max_count > 0:
                record.register_id.write({'max_count': record.register_id.max_count - 1})
        return records