from odoo import models, fields, api

class CrmLeadToStudentWizard(models.TransientModel):
    _name = 'crm.lead.to.student.wizard'
    _description = 'Lead to Student Wizard'

    batch_id = fields.Many2one('op.batch', string='Guruh', required=True)
    lead_id = fields.Many2one('crm.lead', string='Lead', required=False)

    def action_apply(self):
        from odoo.exceptions import UserError

        # Leadlar ro'yxatini aniqlash
        leads = self.env['crm.lead']
        
        if self.lead_id:
            leads = self.lead_id
        elif self.env.context.get('active_ids'):
            selected_leads = self.env['crm.lead'].browse(self.env.context.get('active_ids'))
            leads = selected_leads.filtered(
                lambda l: l.stage_id.name == 'Kursga yozildi' and not l.batch_id
            )
            # Agar tanlanganlarni ichida birorta ham mos keladigani bo'lmasa pop-up chiqaramiz
            if not leads:
                 raise UserError(
                     "Tanlangan leadlar orasida 'Kursga yozildi' bosqichida bo'lgan va "
                     "hali guruhga biriktirilmagan leadlar topilmadi!"
                 )
        else:
            stage = self.env['crm.stage'].search([('name', '=', 'Kursga yozildi')], limit=1)
            if stage:
                leads = self.env['crm.lead'].search([
                    ('stage_id', '=', stage.id),
                    ('batch_id', '=', False)
                ])
            if not leads:
                 raise UserError("Hozirda 'Kursga yozildi' bosqichida guruhga qo'shilishi kerak bo'lgan leadlar yo'q.")
        
        for lead in leads:
            # ─── Ma'lumotlar to'liqligini tekshirish ───
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
                missing.append("Yashash manzili")

            if missing:
                raise UserError(
                    "Lead '%s' ma'lumotlari to'liq emas. Guruhga qo'shish uchun quyidagilarni to'ldiring:\n• "
                    % lead.name + "\n• ".join(missing)
                )

            # Student yaratish (Faqat kerakli maydonlarni aniq ko'rsatamiz)
            student_vals = {
                'first_name': lead.first_name,
                'last_name': lead.last_name,
                'name': lead.name,
                'phone': lead.student_phone,
                'street': lead.address,
                'parent_name': lead.parent_name,
                'parent_phone': lead.parent_phone,
                'gender': 'm', 
                'birth_date': fields.Date.today(),
            }
            
            student = self.env['op.student'].sudo().create(student_vals)
            student.sudo().write({
                'batch_id': self.batch_id.id,
                'parent_name': lead.parent_name,
                'parent_phone': lead.parent_phone,
            })

            # ─── Ota-ona avtomatik yaratish ───
            if lead.parent_name:
                parent_model = self.env['op.parent']
                exist_parent = False
                if lead.parent_phone:
                    exist_parent = parent_model.sudo().search(
                        [('mobile', '=', lead.parent_phone)], limit=1
                    )

                if not exist_parent:
                    parent_partner = self.env['res.partner'].sudo().create({
                        'name': lead.parent_name,
                        'phone': lead.parent_phone or '',
                        'is_parent': True,
                    })
                    rel = self.env['op.parent.relationship'].sudo().search([('name', 'ilike', 'Ota-Onasi')], limit=1)
                    if not rel:
                        rel = self.env['op.parent.relationship'].sudo().search([], limit=1)
                    if not rel:
                        rel = self.env['op.parent.relationship'].sudo().create({'name': 'Ota-Onasi'})

                    parent_model.sudo().create({
                        'name': parent_partner.id,
                        'mobile': lead.parent_phone or '',
                        'relationship_id': rel.id,
                        'student_ids': [(4, student.id)],
                    })
                else:
                    exist_parent.sudo().write({'student_ids': [(4, student.id)]})

            # Kursga yozish
            if lead.course_id:
                self.env['op.student.course'].sudo().create({
                    'student_id': student.id,
                    'course_id': lead.course_id.id,
                    'batch_id': self.batch_id.id,
                    'state': 'running',
                })
                
            lead.sudo().write({
                'batch_id': self.batch_id.id,
                'student_id': student.id,
            })
        
        return {'type': 'ir.actions.act_window_close'}

