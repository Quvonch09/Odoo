from odoo import http, fields
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)

class MoizvonkiController(http.Controller):

    @http.route('/moizvonki/webhook', type='json', auth='none', methods=['POST'], csrf=False)
    def receive_webhook(self, **kwargs):
        data = request.jsonrequest
        _logger.info("Moi Zvonki Webhook received: %s", data)

        event = data.get('event')
        if event == 'call.end':
            call_data = data.get('call', {})
            vals = {
                'name': call_data.get('id'),
                'phone': call_data.get('phone'),
                'direction': 'in' if call_data.get('direction') == 'incoming' else 'out',
                'status': 'answered' if call_data.get('is_answered') else 'missed',
                'duration': call_data.get('duration'),
                'recording_url': call_data.get('recording_url'),
                'start_time': fields.Datetime.to_datetime(call_data.get('start_time')) if call_data.get('start_time') else False,
            }
            
            # Find user by internal number Or email if provided in metadata
            # For now, let's just log it.
            request.env['moizvonki.call'].sudo().create(vals)
            
        return {"status": "ok"}
