import base64
from datetime import datetime, timedelta
from io import BytesIO

import xlsxwriter

from odoo import models, fields, api, _

class OpStudent(models.Model):
    _inherit = 'op.student'
    _order = 'create_date desc'

    parent_name = fields.Char(string="Ota-onasining ismi")
    parent_phone = fields.Char(string="Ota-onasining raqami")
    batch_id = fields.Many2one('op.batch', string="Guruh")
    comment = fields.Text(string="Izohlar") 
    internal_comment = fields.Text(string="Ichki Izoh")

    EXCEL_HEADERS = [
        "Ism-familiya",
        "Yosh",
        "Telefon raqam",
        "Ota-onasining ismi",
        "Ota-onasining telefon raqami",
        "Guruh",
    ]

    @api.model_create_multi
    def create(self, vals_list):
        """ 1. Multi-create qo'llab-quvvatlash va vals_list bilan ishlash """
        for vals in vals_list:
            # Import paytida name bo'lmasa, familya va ismdan yasab olamiz
            if (not vals.get('name') or vals.get('name') == '/') and vals.get('first_name'):
                vals['name'] = f"{vals['first_name']} {vals.get('last_name') or ''}".strip()
            
            # Agar hali ham name bo'lmasa (res_partner_check_name xatosini oldini olish)
            if not vals.get('name'):
                vals['name'] = "Yangi Talaba"

        records = super(OpStudent, self).create(vals_list)
        
        # Har bir yaratilgan record va unga mos vals'ni tekshiramiz
        for rec, vals in zip(records, vals_list):
            if vals.get('internal_comment'):
                rec._create_task_from_comment(vals['internal_comment'])
            
            # Batch berilgan bo'lsa, avtomatik kursga yozish
            if vals.get('batch_id'):
                rec._sync_student_course(vals['batch_id'])

        return records

    def write(self, vals):
        """ 2. Write metodida self (recordset) ichidagi har bir record uchun ishlash """
        # Agar ism o'zgarsa lekin name kelmasa (first_name/last_name o'zgarganda)
        if 'first_name' in vals or 'last_name' in vals:
            for rec in self:
                fname = vals.get('first_name', rec.first_name)
                lname = vals.get('last_name', rec.last_name)
                if not vals.get('name'):
                    vals['name'] = f"{fname or ''} {lname or ''}".strip()

        res = super(OpStudent, self).write(vals)
        
        if 'internal_comment' in vals:
            for rec in self:
                rec._create_task_from_comment(vals['internal_comment'])
        
        if 'batch_id' in vals:
            for rec in self:
                rec._sync_student_course(vals['batch_id'])
                
        return res

    def _sync_student_course(self, batch_id):
        """ Talabani guruhga avtomatik biriktirish """
        self.ensure_one()
        batch = self.env['op.batch'].browse(batch_id)
        if not batch:
            return

        # Tekshiramiz, bu guruhda allaqachon bormi?
        existing_course = self.env['op.student.course'].search([
            ('student_id', '=', self.id),
            ('batch_id', '=', batch.id)
        ], limit=1)

        if not existing_course:
            self.env['op.student.course'].create({
                'student_id': self.id,
                'batch_id': batch.id,
                'course_id': batch.course_id.id,
                'state': 'running',
            })

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

    @api.model
    def get_import_templates(self):
        return [{
            'label': _('Student Excel Shabloni'),
            'template': '/sfera_admission_custom/static/xls/student_import_template.csv'
        }]

    def _get_student_excel_records(self):
        records = self
        if not records and self.env.context.get('active_ids'):
            records = self.browse(self.env.context['active_ids'])
        if not records:
            records = self.search([])
        return records

    def _create_student_excel_attachment(self, workbook_name, rows):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Students')

        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D9EAF7',
            'border': 1,
        })
        cell_format = workbook.add_format({'border': 1})

        for col, header in enumerate(self.EXCEL_HEADERS):
            worksheet.write(0, col, header, header_format)

        for row_idx, row in enumerate(rows, start=1):
            for col_idx, value in enumerate(row):
                worksheet.write(row_idx, col_idx, value or '', cell_format)

        worksheet.set_column(0, 0, 28)
        worksheet.set_column(1, 1, 10)
        worksheet.set_column(2, 4, 24)
        worksheet.set_column(5, 5, 24)
        workbook.close()
        output.seek(0)

        attachment = self.env['ir.attachment'].create({
            'name': workbook_name,
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })
        return attachment

    def action_export_student_excel(self):
        records = self._get_student_excel_records()
        rows = []
        for record in records:
            rows.append([
                record.name,
                record.age_years,
                record.phone,
                record.parent_name,
                record.parent_phone,
                record.batch_id.name,
            ])

        attachment = self._create_student_excel_attachment('students_export.xlsx', rows)
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    def action_download_student_excel_template(self):
        attachment = self._create_student_excel_attachment('student_import_template.xlsx', [])
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
