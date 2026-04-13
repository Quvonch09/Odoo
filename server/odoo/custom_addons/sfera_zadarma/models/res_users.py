from odoo import models, fields

class ResUsers(models.Model):
    _inherit = 'res.users'

    zadarma_extension = fields.Char(
        string='Zadarma Extension',
        help='Internal PBX extension number in Zadarma, for example 101.',
    )
