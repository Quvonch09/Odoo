from odoo import http, fields
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)

class MoizvonkiController(http.Controller):

    @http.route('/moizvonki/webhook', type='json', auth='none', methods=['POST'], csrf=False)
    def receive_webhook_json(self, **kwargs):
        """ Handles application/json webhooks """
        data = request.jsonrequest
        return self._process_webhook(data)

    @http.route('/moizvonki/webhook_http', type='http', auth='none', methods=['POST'], csrf=False)
    def receive_webhook_http(self, **kwargs):
        """ Handles standard form-encoded webhooks """
        # Try JSON first if content-type is json
        if request.httprequest.content_type == 'application/json':
            data = json.loads(request.httprequest.data.decode('utf-8'))
        else:
            data = request.params
        
        self._process_webhook(data)
        return "OK"

    def _process_webhook(self, data):
        _logger.info("Moi Zvonki Webhook received: %s", data)
        event = data.get('event')
        
        if event == 'call.end':
            call_data = data.get('call', {})
            vals = {
                'name': str(call_data.get('id') or ''),
                'phone': str(call_data.get('phone') or ''),
                'direction': 'in' if call_data.get('direction') == 'incoming' else 'out',
                'status': 'answered' if call_data.get('is_answered') else 'missed',
                'duration': int(call_data.get('duration') or 0),
                'recording_url': str(call_data.get('recording_url') or ''),
                'start_time': fields.Datetime.now(), # Default to now if not provided
            }
            
            # Start time formatting if available
            st_raw = call_data.get('start_time')
            if st_raw:
                try:
                    vals['start_time'] = fields.Datetime.to_datetime(st_raw)
                except:
                    pass

            # Create call record as superuser
            request.env['moizvonki.call'].sudo().create(vals)
            
        return {"status": "ok"}
