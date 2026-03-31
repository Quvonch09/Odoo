from odoo import models, fields, api, _
from odoo.exceptions import UserError

class OpAdmission(models.Model):
    _inherit = 'op.admission'

    @api.model_create_multi
    def create(self, vals_list):
        records = super(OpAdmission, self).create(vals_list)
        
        for record in records:
            if record.register_id:
                # Registraturadagi joylar sonini kamaytirish
                register = record.register_id.sudo()
                if register.max_count > 0:
                    register.write({
                        'max_count': register.max_count - 1
                    })
        return records

