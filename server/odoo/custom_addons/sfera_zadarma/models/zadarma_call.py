import base64
import hashlib
import hmac
import json
import logging
from datetime import datetime
from urllib.parse import urlencode

import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ZadarmaCall(models.Model):
    _name = 'zadarma.call'
    _description = 'Zadarma Call'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'call_start desc, id desc'

    name = fields.Char(required=True, tracking=True)
    pbx_call_id = fields.Char(string='PBX Call ID', index=True, copy=False, tracking=True)
    call_id_with_rec = fields.Char(string='Recording Call ID', copy=False)
    event = fields.Char(tracking=True)
    direction = fields.Selection([('in', 'Incoming'), ('out', 'Outgoing')], default='out', tracking=True)
    status = fields.Selection([
        ('initiated', 'Initiated'),
        ('ringing', 'Ringing'),
        ('answered', 'Answered'),
        ('busy', 'Busy'),
        ('cancel', 'Cancelled'),
        ('no_answer', 'No Answer'),
        ('failed', 'Failed'),
        ('unknown', 'Unknown'),
    ], default='initiated', tracking=True)
    phone = fields.Char(string='Phone Number', tracking=True)
    caller_id = fields.Char(string='Caller', tracking=True)
    called_did = fields.Char(string='Called DID', tracking=True)
    destination = fields.Char(string='Destination', tracking=True)
    internal_extension = fields.Char(string='Internal Extension', tracking=True)
    duration = fields.Integer(string='Duration (seconds)', tracking=True)
    call_start = fields.Datetime(tracking=True)
    recording_url = fields.Char(string='Recording URL', tracking=True)
    is_recorded = fields.Boolean(tracking=True)
    payload = fields.Text(string='Raw Payload')
    lead_id = fields.Many2one('crm.lead', string='Lead', tracking=True)
    partner_id = fields.Many2one('res.partner', string='Contact', tracking=True)
    user_id = fields.Many2one('res.users', string='Employee', tracking=True)

    @api.model
    def _normalize_phone(self, phone):
        if not phone:
            return False
        normalized = ''.join(ch for ch in str(phone) if ch.isdigit())
        if normalized.startswith('00'):
            normalized = normalized[2:]
        return normalized or False

    @api.model
    def _normalize_extension(self, extension):
        return (extension or '').strip() or False

    @api.model
    def _parse_call_start(self, value):
        if not value:
            return fields.Datetime.now()
        if isinstance(value, datetime):
            return value
        value = str(value).strip()
        if value.isdigit():
            return datetime.utcfromtimestamp(int(value))
        try:
            return fields.Datetime.to_datetime(value)
        except Exception:
            return fields.Datetime.now()

    @api.model
    def _phone_search_variants(self, phone):
        normalized = self._normalize_phone(phone)
        if not normalized:
            return []
        variants = [normalized]
        if len(normalized) > 9:
            variants.append(normalized[-9:])
        if len(normalized) > 12:
            variants.append(normalized[-12:])
        return list(dict.fromkeys(variants))

    @api.model
    def _find_related_records(self, phone):
        partner = self.env['res.partner']
        lead = self.env['crm.lead']
        for variant in self._phone_search_variants(phone):
            like_value = '%' + variant
            partner = self.env['res.partner'].search(
                ['|', ('phone', 'ilike', like_value), ('mobile', 'ilike', like_value)],
                limit=1,
            )
            if not lead:
                lead = self.env['crm.lead'].search(
                    ['|', '|', ('student_phone', 'ilike', like_value), ('parent_phone', 'ilike', like_value), ('phone', 'ilike', like_value)],
                    limit=1,
                )
            if partner or lead:
                return partner, lead
        return partner, lead

    @api.model
    def _find_user_by_extension(self, extension):
        extension = self._normalize_extension(extension)
        if not extension:
            return self.env['res.users']
        return self.env['res.users'].sudo().search([('zadarma_extension', '=', extension)], limit=1)

    @api.model
    def _get_zadarma_credentials(self):
        icp = self.env['ir.config_parameter'].sudo()
        api_key = (icp.get_param('sfera_zadarma.api_key') or '').strip()
        secret_key = (icp.get_param('sfera_zadarma.secret_key') or '').strip()
        if not api_key or not secret_key:
            raise ValidationError(_("Zadarma API Key or Secret Key is not configured."))
        return api_key, secret_key

    @api.model
    def _build_auth_header(self, method, params, api_key, secret_key):
        encoded_params = urlencode(sorted((params or {}).items()))
        signing_string = f"{method}{encoded_params}{hashlib.md5(encoded_params.encode('utf-8')).hexdigest()}"
        signature_hex = hmac.new(
            secret_key.encode('utf-8'),
            signing_string.encode('utf-8'),
            hashlib.sha1,
        ).hexdigest()
        signature = base64.b64encode(signature_hex.encode('utf-8')).decode('utf-8')
        return {'Authorization': f'{api_key}:{signature}'}

    @api.model
    def _zadarma_api_request(self, method, params=None, http_method='GET', timeout=20):
        params = dict(params or {})
        api_key, secret_key = self._get_zadarma_credentials()
        headers = self._build_auth_header(method, params, api_key, secret_key)
        url = f'https://api.zadarma.com{method}'
        request_kwargs = {'headers': headers, 'timeout': timeout}
        if http_method.upper() == 'GET':
            request_kwargs['params'] = params
        else:
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
            request_kwargs['data'] = params
        try:
            response = requests.request(http_method.upper(), url, **request_kwargs)
            try:
                result = response.json()
            except ValueError:
                result = {}
        except requests.exceptions.RequestException as exc:
            raise ValidationError(_("Failed to reach Zadarma: %s") % exc) from exc

        if response.status_code == 401:
            raise ValidationError(_(
                "Zadarma rejected the credentials or request signature. "
                "Check that you entered the API key/secret from the Zadarma API section, not SIP credentials."
            ))
        if response.status_code >= 400:
            message = result.get('message') if isinstance(result, dict) else False
            raise ValidationError(_("Zadarma HTTP error %(code)s: %(message)s", code=response.status_code, message=message or _('Unknown error')))
        if not isinstance(result, dict):
            raise ValidationError(_("Zadarma returned an invalid response."))

        if result.get('status') != 'success':
            raise ValidationError(_("Zadarma error: %s") % (result.get('message') or _('Unknown error')))
        return result

    @api.model
    def _fetch_recording_url(self, call_id_with_rec, pbx_call_id=None):
        if not call_id_with_rec:
            return False
        params = {'call_id_with_rec': call_id_with_rec, 'format': 'json'}
        if pbx_call_id:
            params['pbx_call_id'] = pbx_call_id
        try:
            result = self._zadarma_api_request('/v1/pbx/record/request/', params=params)
        except ValidationError as exc:
            _logger.warning("Zadarma recording fetch failed for %s: %s", call_id_with_rec, exc)
            return False

        return (
            result.get('link')
            or result.get('url')
            or result.get('download_link')
            or result.get('record_url')
            or False
        )

    @api.model
    def action_make_call(self, phone, lead=None, partner=None):
        phone = self._normalize_phone(phone)
        if not phone:
            raise UserError(_("Please provide a valid phone number."))

        extension = self._normalize_extension(self.env.user.zadarma_extension)
        if not extension:
            raise UserError(_("Your user does not have a Zadarma extension configured."))

        result = self._zadarma_api_request(
            '/v1/request/callback/',
            params={'from': extension, 'to': phone, 'sip': extension, 'format': 'json'},
        )

        body = _("Zadarma callback requested to %(phone)s from extension %(extension)s.", phone=phone, extension=extension)
        if lead:
            lead.message_post(body=body)
        if partner:
            partner.message_post(body=body)

        self.create({
            'name': _('Callback %s') % fields.Datetime.now(),
            'event': 'CALLBACK_REQUEST',
            'direction': 'out',
            'status': 'initiated',
            'phone': phone,
            'destination': phone,
            'internal_extension': extension,
            'call_start': fields.Datetime.now(),
            'lead_id': lead.id if lead else False,
            'partner_id': partner.id if partner else False,
            'user_id': self.env.user.id,
            'payload': json.dumps(result, ensure_ascii=True),
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Zadarma'),
                'message': _("Callback request sent. Check your Zadarma device or softphone."),
                'type': 'success',
                'sticky': False,
            }
        }

    @api.model
    def _status_from_payload(self, event, payload):
        disposition = (payload.get('disposition') or '').strip().lower()
        if event in ('NOTIFY_START', 'NOTIFY_INTERNAL', 'NOTIFY_OUT_START'):
            return 'ringing'
        if event == 'NOTIFY_ANSWER':
            return 'answered'
        mapping = {
            'answered': 'answered',
            'answer': 'answered',
            'busy': 'busy',
            'cancel': 'cancel',
            'no answer': 'no_answer',
            'noanswer': 'no_answer',
            'failed': 'failed',
        }
        return mapping.get(disposition, 'unknown')

    @api.model
    def _event_signature_payload(self, event, payload):
        if event in ('NOTIFY_START', 'NOTIFY_INTERNAL', 'NOTIFY_END', 'NOTIFY_IVR'):
            return f"{payload.get('caller_id', '')}{payload.get('called_did', '')}{payload.get('call_start', '')}"
        if event == 'NOTIFY_ANSWER':
            return f"{payload.get('caller_id', '')}{payload.get('destination', '')}{payload.get('call_start', '')}"
        if event in ('NOTIFY_OUT_START', 'NOTIFY_OUT_END'):
            return f"{payload.get('internal', '')}{payload.get('destination', '')}{payload.get('call_start', '')}"
        if event == 'NOTIFY_RECORD':
            return f"{payload.get('pbx_call_id', '')}{payload.get('call_id_with_rec', '')}"
        return False

    @api.model
    def validate_webhook_signature(self, payload, signature):
        if not signature:
            return False
        _, secret_key = self._get_zadarma_credentials()
        event = payload.get('event')
        signature_payload = self._event_signature_payload(event, payload)
        if signature_payload is False:
            return True
        expected = base64.b64encode(
            hmac.new(secret_key.encode('utf-8'), signature_payload.encode('utf-8'), hashlib.sha1).digest()
        ).decode('utf-8')
        return hmac.compare_digest(expected, signature)

    @api.model
    def _call_values_from_payload(self, payload):
        event = payload.get('event') or 'UNKNOWN'
        direction = 'out' if event.startswith('NOTIFY_OUT') else 'in'
        phone = payload.get('destination') if direction == 'out' else payload.get('caller_id')
        partner, lead = self._find_related_records(phone)
        extension = payload.get('internal') or payload.get('last_internal')
        user = self._find_user_by_extension(extension)

        values = {
            'name': payload.get('pbx_call_id') or payload.get('call_id_with_rec') or event,
            'pbx_call_id': payload.get('pbx_call_id'),
            'call_id_with_rec': payload.get('call_id_with_rec'),
            'event': event,
            'direction': direction,
            'status': self._status_from_payload(event, payload),
            'phone': self._normalize_phone(phone) or phone,
            'caller_id': payload.get('caller_id'),
            'called_did': payload.get('called_did'),
            'destination': payload.get('destination'),
            'internal_extension': extension,
            'duration': int(payload.get('duration') or 0),
            'call_start': self._parse_call_start(payload.get('call_start')),
            'is_recorded': str(payload.get('is_recorded') or '0') in ('1', 'true', 'True'),
            'payload': json.dumps(payload, ensure_ascii=True),
            'lead_id': lead.id if lead else False,
            'partner_id': partner.id if partner else False,
            'user_id': user.id if user else False,
        }
        if event == 'NOTIFY_RECORD':
            values['recording_url'] = self._fetch_recording_url(values['call_id_with_rec'], values['pbx_call_id'])
            values['is_recorded'] = True
            values['status'] = 'answered'
        return values

    @api.model
    def process_webhook(self, payload):
        event = payload.get('event')
        if not event:
            return {'status': 'ignored', 'reason': 'missing_event'}

        values = self._call_values_from_payload(payload)
        if values.get('pbx_call_id'):
            domain = [('pbx_call_id', '=', values['pbx_call_id'])]
        elif values.get('call_id_with_rec'):
            domain = [('call_id_with_rec', '=', values['call_id_with_rec'])]
        else:
            domain = [('name', '=', values['name'])]
        call = self.search(domain, limit=1)
        if call:
            call.write(values)
        else:
            call = self.create(values)

        if event in ('NOTIFY_END', 'NOTIFY_OUT_END', 'NOTIFY_RECORD'):
            call._post_call_summary()
        return {'status': 'ok', 'call_id': call.id}

    def _post_call_summary(self):
        status_labels = dict(self._fields['status'].selection)
        for record in self:
            direction_label = _('Incoming') if record.direction == 'in' else _('Outgoing')
            status_label = status_labels.get(record.status, record.status)
            body = _(
                "<b>Zadarma call</b><br/>"
                "Direction: %(direction)s<br/>"
                "Phone: %(phone)s<br/>"
                "Status: %(status)s<br/>"
                "Duration: %(duration)s sec",
                direction=direction_label,
                phone=record.phone or '-',
                status=status_label,
                duration=record.duration or 0,
            )
            if record.recording_url:
                body += _("<br/>Recording: <a href=\"%s\" target=\"_blank\">download</a>") % record.recording_url
            if record.lead_id:
                record.lead_id.message_post(body=body)
            if record.partner_id:
                record.partner_id.message_post(body=body)
