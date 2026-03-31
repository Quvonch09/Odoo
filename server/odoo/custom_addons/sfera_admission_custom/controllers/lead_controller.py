from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class LeadController(http.Controller):
    @http.route('/lead/form', type='http', auth='public', website=True)
    def open_lead_form(self, **kwargs):
        """
        Instagram uchun maxsus forma sahifasi.
        Link: http://localhost:8069/lead/form
        """
        return request.render('sfera_admission_custom.leads_form_page')

    @http.route('/lead/submit', type='http', auth='public', methods=['POST'], website=True, csrf=True)
    def submit_lead_form(self, **kwargs):
        """
        Forma yuborilganda lead yaratish.
        """
        try:
            first_name = kwargs.get('first_name')
            phone = kwargs.get('student_phone')
            
            if not first_name or not phone:
                return "Xatolik: Ism va Telefon kiritilishi shart!"

            vals = {
                'first_name': first_name,
                'last_name': kwargs.get('last_name', ''),
                'student_phone': phone,
                'lead_source': kwargs.get('lead_source', 'instagram'),
                'type': 'opportunity',
            }
            
            # Lead yaratish
            request.env['crm.lead'].sudo().create(vals)
            
            _logger.info("Instagram'dan yangi lead yaratildi: %s", first_name)
            
            # Rahmat sahifasini ko'rsatish
            return request.render('sfera_admission_custom.leads_thanks_page')
        except Exception as e:
            _logger.error("Lead yaratib bo'lmadi: %s", str(e))
            return "Xatolik yuz berdi: %s" % str(e)

