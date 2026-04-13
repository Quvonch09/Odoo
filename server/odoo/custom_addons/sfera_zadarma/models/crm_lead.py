from odoo import _, models
from odoo.exceptions import UserError


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    def action_zadarma_call(self):
        self.ensure_one()
        phone_number = getattr(self, 'student_phone', False) or self.phone or self.mobile
        return self.env['zadarma.call'].action_make_call(phone_number, lead=self)

    def action_zadarma_call_parent(self):
        self.ensure_one()
        phone_number = getattr(self, 'parent_phone', False)
        if not phone_number:
            raise UserError(_("Please provide a parent phone number."))
        return self.env['zadarma.call'].action_make_call(phone_number, lead=self)
