from datetime import date

from odoo import models, fields, api

class OpStudent(models.Model):
    _inherit = 'op.student'

    # Talabaga bitta guruhni biriktirish uchun field
    batch_id = fields.Many2one('op.batch', string='Guruh (Batch)')
    age_years = fields.Integer(
        string='Yoshi',
        compute='_compute_age_years',
        inverse='_inverse_age_years',
        help="Yosh kiritilganda tug'ilgan sana avtomatik 1-yanvar qilib hisoblanadi."
    )

    @api.depends('birth_date')
    def _compute_age_years(self):
        current_year = fields.Date.today().year
        for record in self:
            record.age_years = current_year - record.birth_date.year if record.birth_date else 0

    def _inverse_age_years(self):
        current_year = fields.Date.today().year
        for record in self:
            if record.age_years and record.age_years > 0:
                record.birth_date = date(current_year - record.age_years, 1, 1)
            elif record.age_years == 0:
                record.birth_date = False
