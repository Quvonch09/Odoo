from odoo import models, fields, api

class OpFaculty(models.Model):
    _inherit = 'op.faculty'

    @api.model
    def action_sync_faculty_users(self):
        # Barcha o'qituvchilarni olamiz
        faculties = self.search([])
        for faculty in faculties:
            # Ismi mos keladigan userni qidiramiz
            user = self.env['res.users'].search([('name', '=', faculty.name)], limit=1)
            if user:
                # Agar user topilsa, bog'laymiz
                faculty.write({
                    'user_id': user.id,
                    'partner_id': user.partner_id.id
                })
        return True