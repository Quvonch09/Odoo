from odoo import models, fields, api, _

# class OpAdmissionRegister(models.Model):
#     _inherit = 'op.admission.register'

#     # XML xatosini yo'qotish uchun ushbu maydonni e'lon qilamiz
#     course_fees_amount = fields.Float(string='Course Fees Amount')
#     min_count = fields.Integer(default=1)

#     def action_create_new_lead(self):
#         self.ensure_one()
#         return {
#             'name': _('Yangi Ariza'),
#             'type': 'ir.actions.act_window',
#             'res_model': 'op.admission',
#             'view_mode': 'form',
#             'target': 'current',
#             'context': {
#                 'default_register_id': self.id,
#                 'default_course_id': self.course_id.id,
#                 'default_custom_fees': self.course_fees_amount,
#                 'default_fees': self.course_fees_amount,
#             }
#         }

# class OpAdmission(models.Model):
#     _inherit = 'op.admission'

#     # Mavjud custom fieldlar
#     custom_fees = fields.Float(string="Course Fees")
#     batch_id = fields.Many2one('op.batch', required=False)

#     @api.onchange('custom_fees')
#     def _onchange_custom_fees_sync(self):
#         if self.custom_fees:
#             self.fees = self.custom_fees

#     def submit_form(self):
#         """ 
#         Submit bosilganda statusni Done ga o'tkazish 
#         """
#         # 1. Standart mantiqni ishga tushirish
#         res = super(OpAdmission, self).submit_form()
        
#         # 2. Statusni bir yo'la Done holatiga o'tkazish
#         # OpenEduCat da 'done' statusi qabul qilingan yakuniy holat
#         self.write({'state': 'done'})
        
#         return res

class OpAdmissionRegister(models.Model):
    _inherit = 'op.admission.register'

    # Ikkala field ham qolsin (eski kodlar buzilmasligi uchun)
    custom_fees = fields.Float(string='Course Fees Amount')
    course_fees_amount = fields.Float(string='Course Fees Amount Lite')
    custom_fees = fields.Float(string="Course Fees")

    def action_create_new_lead(self):
        self.ensure_one()
        # Qaysi birida summa bo'lsa, o'shani olamiz
        amount = self.course_fees_amount or self.custom_fees
        
        return {
            'name': _('Yangi Ariza'),
            'type': 'ir.actions.act_window',
            'res_model': 'op.admission',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_register_id': self.id,
                'default_course_id': self.course_id.id,
                'default_fees': amount,  # Standart fieldga qiymat berish
                'default_custom_fees': amount, # Sizning custom fieldingizga ham
            }
        }

class OpAdmission(models.Model):
    _inherit = 'op.admission'

    # Mavjud fieldlar va metodlar (bularga tegmaymiz)
    custom_fees = fields.Float(string="Course Fees")

    # 1. Onchange: Register tanlanganda summani yangilash
    @api.onchange('register_id')
    def _onchange_register_fees_sync(self):
        if self.register_id:
            # Registerdagi ikki fielddan birini (to'lasini) oladi
            amount = self.register_id.course_fees_amount or self.register_id.custom_fees
            if amount > 0:
                self.fees = amount
                self.custom_fees = amount

    # 2. Create: Saqlash vaqtida summani kafolatlash (Sizning eski max_count mantiqingiz bilan)
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('register_id') and not vals.get('fees'):
                reg = self.env['op.admission.register'].browse(vals['register_id'])
                amount = reg.course_fees_amount or reg.custom_fees
                if amount:
                    vals['fees'] = amount
        
        # ESKI MANTIQ: Super() chaqirish va max_count kamaytirish
        records = super(OpAdmission, self).create(vals_list)
        
        # for record in records:
        #     if record.register_id and record.register_id.max_count > 0:
        #         record.register_id.write({'max_count': record.register_id.max_count - 1})
        # return records

    # Sizning eski submit_form kodingiz o'zgarishsiz qoladi
    def submit_form(self):
        res = super(OpAdmission, self).submit_form()
        self.write({'state': 'done'})
        return res