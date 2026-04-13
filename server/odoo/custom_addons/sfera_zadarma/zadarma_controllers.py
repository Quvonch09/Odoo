import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class ZadarmaController(http.Controller):

    @http.route('/zadarma/webhook', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def zadarma_webhook(self, **kwargs):
        echo = request.httprequest.args.get('zd_echo')
        if echo:
            return request.make_response(echo)

        payload = dict(request.params)
        payload.pop('csrf_token', None)
        signature = (
            request.httprequest.headers.get('Signature')
            or request.httprequest.headers.get('signature')
            or payload.get('signature')
        )

        _logger.info('Zadarma webhook received: %s', payload)

        try:
            model = request.env['zadarma.call'].sudo()
            if not model.validate_webhook_signature(payload, signature):
                _logger.warning('Rejected Zadarma webhook due to invalid signature: %s', payload)
                return request.make_response('invalid signature', status=403)
            model.process_webhook(payload)
        except Exception:
            _logger.exception('Failed to process Zadarma webhook')
            return request.make_response('error', status=500)

        return request.make_response('ok')
